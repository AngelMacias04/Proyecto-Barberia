# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Barbero(models.Model):
    id_barbero = models.CharField(primary_key=True, max_length=10)
    nombre = models.CharField(max_length=50, blank=True, null=True)
    edad = models.CharField(max_length=3, blank=True, null=True)
    telefono = models.CharField(max_length=10, blank=True, null=True)
    tipopago = models.ForeignKey('Pagos', models.DO_NOTHING, db_column='tipoPago', blank=True, null=True)  # Field name made lowercase.
    user = models.CharField(max_length=15, blank=True, null=True)
    password = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'barbero'


class Citas(models.Model):
    id_cita = models.CharField(primary_key=True, max_length=20)
    id_barbero = models.ForeignKey(Barbero, models.DO_NOTHING, db_column='id_barbero', blank=True, null=True)
    id_cliente = models.ForeignKey('Cliente', models.DO_NOTHING, db_column='id_cliente', blank=True, null=True)
    dia = models.CharField(max_length=10, blank=True, null=True)
    hora = models.CharField(max_length=6, blank=True, null=True)
    servicio1 = models.ForeignKey('Servicios', models.DO_NOTHING, db_column='servicio1', blank=True, null=True)
    servicio2 = models.ForeignKey('Servicios', models.DO_NOTHING, db_column='servicio2', related_name='citas_servicio2_set', blank=True, null=True)
    servicio3 = models.ForeignKey('Servicios', models.DO_NOTHING, db_column='servicio3', related_name='citas_servicio3_set', blank=True, null=True)
    total = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'citas'


class Cliente(models.Model):
    id_cliente = models.CharField(primary_key=True, max_length=10)
    nombre = models.CharField(max_length=50, blank=True, null=True)
    edad = models.CharField(max_length=3, blank=True, null=True)
    telefono = models.CharField(max_length=10, blank=True, null=True)
    user = models.CharField(max_length=15, blank=True, null=True)
    password = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cliente'


class Duenio(models.Model):
    id_duenio = models.CharField(primary_key=True, max_length=5)
    user = models.CharField(max_length=15, blank=True, null=True)
    password = models.CharField(max_length=10, blank=True, null=True)
    name = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'duenio'


class Pagos(models.Model):
    id_tipodepago = models.CharField(db_column='id_tipoDePago', primary_key=True, max_length=10)  # Field name made lowercase.
    tipodepago = models.CharField(db_column='tipoDePago', max_length=25, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'pagos'


class Resultados(models.Model):
    id_resultado = models.CharField(primary_key=True, max_length=10)
    id_barbero = models.ForeignKey(Barbero, models.DO_NOTHING, db_column='id_barbero', blank=True, null=True)
    id_cita = models.ForeignKey(Citas, models.DO_NOTHING, db_column='id_cita', blank=True, null=True)
    total = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'resultados'


class Servicios(models.Model):
    id_servicio = models.CharField(primary_key=True, max_length=10)
    servicio = models.CharField(max_length=50, blank=True, null=True)
    precio = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'servicios'
