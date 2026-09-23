from django.db import models
from django.contrib.postgres.fields import JSONField


class Collection(models.Model):
    id = models.CharField(primary_key=True, max_length=200)
    nombre = models.CharField(max_length=500)
    descripcion = models.TextField(blank=True)
    limitations = JSONField(default=list)

    class Meta:
        verbose_name = "Colección"
        verbose_name_plural = "Colecciones"

    def __str__(self):
        return f"{self.id} — {self.nombre}"


class Concept(models.Model):
    id = models.CharField(primary_key=True, max_length=200)
    nombre = models.CharField(max_length=500)
    descripcion = models.TextField(blank=True)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='concepts')
    frecuencia = models.CharField(max_length=50, blank=True)
    unidad = models.CharField(max_length=100, blank=True)
    sample_questions = JSONField(default=list)
    limitations = JSONField(default=list)
    dimensiones = JSONField()
    dimensiones_compatibles = JSONField(default=list)

    class Meta:
        verbose_name = "Concepto"
        verbose_name_plural = "Conceptos"

    def __str__(self):
        return f"{self.id} — {self.nombre}"
