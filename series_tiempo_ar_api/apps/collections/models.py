from django.db import models
from django.contrib.postgres.fields import JSONField


class Collection(models.Model):
    id = models.CharField(primary_key=True, max_length=200)
    nombre = models.CharField(max_length=500)
    descripcion = models.TextField(blank=True)

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
    # [{id, nombre, valores_posibles: [...]}]
    dimensiones = JSONField()
    # [[dim1, dim2], [dim1, dim3]] — grupos de dimensiones que se pueden combinar
    dimensiones_compatibles = JSONField(default=list)

    class Meta:
        verbose_name = "Concepto"
        verbose_name_plural = "Conceptos"

    def __str__(self):
        return f"{self.id} — {self.nombre}"
