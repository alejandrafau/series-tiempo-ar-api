import json

from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.conf.urls import url
from django.urls import reverse

from .models import Collection, Concept


class UnicodeJSONField(forms.CharField):
    def prepare_value(self, value):
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False, indent=2)

    def to_python(self, value):
        if value is None or value == '':
            return None
        if isinstance(value, (dict, list)):
            return value
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f'JSON inválido: {e}')


class ConceptForm(forms.ModelForm):
    dimensiones = UnicodeJSONField(widget=forms.Textarea)
    dimensiones_compatibles = UnicodeJSONField(widget=forms.Textarea, required=False, initial=[])

    class Meta:
        model = Concept
        fields = '__all__'


class CollectionFileForm(forms.Form):
    archivo = forms.FileField(
        label="Archivo JSON",
        help_text='JSON con estructura {"collections": [{id, nombre, descripcion, concepts: [...]}]}'
    )


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')

    def get_readonly_fields(self, request, obj=None):
        return ('id',) if obj else ()

    def get_urls(self):
        custom = [
            url(r'^cargar/$', self.admin_site.admin_view(self.cargar_view), name='collections_cargar'),
        ]
        return custom + super().get_urls()

    def cargar_view(self, request):
        if request.method == 'POST':
            form = CollectionFileForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    data = json.loads(request.FILES['archivo'].read().decode('utf-8'))
                    n_col, n_con = _procesar_collections(data)
                    messages.success(request, f"Cargadas {n_col} colecciones y {n_con} conceptos.")
                    return HttpResponseRedirect(reverse('admin:collections_collection_changelist'))
                except Exception as e:
                    messages.error(request, f"Error al procesar el archivo: {e}")
        else:
            form = CollectionFileForm()

        context = {
            **self.admin_site.each_context(request),
            'form': form,
            'title': 'Cargar colecciones desde JSON',
            'opts': self.model._meta,
        }
        return render(request, 'admin/collections/cargar.html', context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['cargar_url'] = reverse('admin:collections_cargar')
        return super().changelist_view(request, extra_context=extra_context)


def _procesar_collections(data):
    n_col = n_con = 0
    for col_data in data.get('collections', []):
        collection, _ = Collection.objects.update_or_create(
            id=col_data['id'],
            defaults={
                'nombre': col_data.get('nombre', ''),
                'descripcion': col_data.get('descripcion', ''),
            }
        )
        n_col += 1
        for concept_data in col_data.get('concepts', []):
            Concept.objects.update_or_create(
                id=concept_data['id'],
                defaults={
                    'nombre': concept_data.get('nombre', ''),
                    'descripcion': concept_data.get('descripcion', ''),
                    'collection': collection,
                    'dimensiones': concept_data.get('dimensiones', []),
                    'dimensiones_compatibles': concept_data.get('dimensiones_compatibles', []),
                }
            )
            n_con += 1
    return n_col, n_con


@admin.register(Concept)
class ConceptAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'collection')
    list_filter = ('collection',)
    form = ConceptForm

    def get_readonly_fields(self, request, obj=None):
        return ('id',) if obj else ()
