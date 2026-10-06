import pymysql
pymysql.install_as_MySQLdb()

# Parche para evitar que Django bloquee versiones de MySQL anteriores a la 8.4
from django.db.backends.mysql.base import DatabaseWrapper
def _is_mysql_8_4(self):
    return True
DatabaseWrapper.is_muj = property(_is_mysql_8_4) # O sobrescribir la verificación de versión:

from django.db.backends.base.base import BaseDatabaseWrapper
original_check_version = BaseDatabaseWrapper.check_database_version_supported

def custom_check_version(self):
    if self.vendor == 'mysql':
        # Permitir versiones de MySQL 8.0 o superiores
        return True
    return original_check_version(self)

BaseDatabaseWrapper.check_database_version_supported = custom_check_version