# Generated manually to fix foreign key mismatch for both ImpactoAmbiental and Transaccion

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0003_remove_prenda_id_prenda_id_prenda'),
    ]

    operations = [
        migrations.RunSQL(
            """
            BEGIN;
            PRAGMA foreign_keys = OFF;

            -- Fix impacto_ambiental table
            ALTER TABLE impacto_ambiental RENAME TO impacto_ambiental_old;
            CREATE TABLE impacto_ambiental (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prenda_id INTEGER NOT NULL REFERENCES prenda (id_prenda),
                carbono_evitar_kg DECIMAL(8,2) NULL,
                energia_ahorrada_kwh DECIMAL(8,2) NULL,
                fecha_calculo DATETIME NULL
            );
            INSERT INTO impacto_ambiental SELECT * FROM impacto_ambiental_old;
            DROP TABLE impacto_ambiental_old;

            -- Fix transaccion table
            ALTER TABLE transaccion RENAME TO transaccion_old;
            CREATE TABLE transaccion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prenda_id INTEGER NOT NULL REFERENCES prenda (id_prenda),
                tipo_id INTEGER NOT NULL REFERENCES tipo_transaccion (id),
                user_origen_id INTEGER NOT NULL REFERENCES usuario (id_usuario),
                user_destino_id INTEGER NULL REFERENCES usuario (id_usuario),
                fundacion_id INTEGER NULL REFERENCES fundacion (id_fundacion),
                campana_id INTEGER NULL REFERENCES campana_fundacion (id),
                fecha_transaccion DATETIME NULL,
                estado VARCHAR(20) NOT NULL,
                destino_final VARCHAR(300) NULL,
                fecha_entrega DATETIME NULL,
                en_disputa BOOLEAN NOT NULL DEFAULT 0,
                razon_disputa TEXT NULL,
                reportado_por_id INTEGER NULL REFERENCES usuario (id_usuario),
                fecha_disputa DATETIME NULL,
                direccion_retiro VARCHAR(300) NULL,
                direccion_entrega VARCHAR(300) NULL,
                peso_kg DECIMAL(5,2) NULL,
                dimensiones VARCHAR(100) NULL,
                codigo_seguimiento_envio VARCHAR(100) NULL,
                costo_envio DECIMAL(10,2) NULL,
                courier VARCHAR(50) NULL
            );
            INSERT INTO transaccion SELECT * FROM transaccion_old;
            DROP TABLE transaccion_old;

            PRAGMA foreign_keys = ON;
            COMMIT;
            """,
            reverse_sql="SELECT 1;"  # Not reversible
        ),
    ]
