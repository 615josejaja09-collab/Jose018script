import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import random
import string
import datetime
import json
import io
import requests
from keep_alive import keep_alive

# Cargar configuración
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", 0))
OWNER_USER_ID = int(os.getenv("OWNER_USER_ID", 0))
SECOND_OWNER_ID = 946701610522931250
ROL_COMPRADOR_ID = int(os.getenv("ROL_COMPRADOR_ID", 0))
API_URL = "https://DiscreteOfficialExponent.615josejaja09.repl.co"

# Base de datos
DB_FILE = 'key_database.json'

def load_database():
    """Carga la base de datos desde el archivo JSON"""
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ Base de datos cargada: {len(data)} claves")

            # Convertir strings de fecha a objetos datetime
            for key, key_data in data.items():
                if key_data.get('expires_at'):
                    try:
                        key_data['expires_at'] = datetime.datetime.fromisoformat(key_data['expires_at'])
                    except:
                        key_data['expires_at'] = None
                if key_data.get('redeemed_at'):
                    try:
                        key_data['redeemed_at'] = datetime.datetime.fromisoformat(key_data['redeemed_at'])
                    except:
                        key_data['redeemed_at'] = None
                if key_data.get('created_at'):
                    try:
                        key_data['created_at'] = datetime.datetime.fromisoformat(key_data['created_at'])
                    except:
                        key_data['created_at'] = datetime.datetime.now(datetime.timezone.utc)

            return data
    except FileNotFoundError:
        print("🆕 Creando nueva base de datos...")
        return {}
    except json.JSONDecodeError:
        print("❌ Error en formato JSON, creando nueva base de datos...")
        return {}
    except Exception as e:
        print(f"❌ Error cargando base de datos: {e}")
        return {}

def save_database():
    """Guarda la base de datos en el archivo JSON"""
    try:
        # Crear copia para serialización
        data_to_save = {}
        for key, key_data in KEY_DATABASE.items():
            data_to_save[key] = key_data.copy()

            # Convertir datetime a string para JSON
            if isinstance(key_data.get('expires_at'), datetime.datetime):
                data_to_save[key]['expires_at'] = key_data['expires_at'].isoformat()
            if isinstance(key_data.get('redeemed_at'), datetime.datetime):
                data_to_save[key]['redeemed_at'] = key_data['redeemed_at'].isoformat()
            if isinstance(key_data.get('created_at'), datetime.datetime):
                data_to_save[key]['created_at'] = key_data['created_at'].isoformat()

        # Guardar en archivo
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)

        print(f"💾 Base de datos guardada: {len(KEY_DATABASE)} claves")

        # Sincronizar con servidor de autenticación
        try:
            sync_data = {}
            for key, key_data in KEY_DATABASE.items():
                sync_data[key] = {
                    'status': key_data.get('status', 'unused'),
                    'user_id': key_data.get('user_id'),
                    'username': key_data.get('username'),
                    'hwid': key_data.get('hwid'),
                    'expires_at': key_data.get('expires_at').isoformat() if isinstance(key_data.get('expires_at'), datetime.datetime) else key_data.get('expires_at'),
                    'redeemed_at': key_data.get('redeemed_at').isoformat() if isinstance(key_data.get('redeemed_at'), datetime.datetime) else key_data.get('redeemed_at')
                }

            response = requests.post(f"{API_URL}/sync-keys", json=sync_data, timeout=10)
            if response.status_code == 200:
                print("✅ Base de datos sincronizada con servidor de autenticación")
            else:
                print(f"⚠️ Error en sincronización: {response.status_code}")
        except Exception as e:
            print(f"⚠️ No se pudo sincronizar con servidor: {e}")

    except Exception as e:
        print(f"❌ Error crítico guardando base de datos: {e}")

# Cargar base de datos al inicio
KEY_DATABASE = load_database()

# =======================================================
# CLASES DE LA INTERFAZ
# =======================================================

class RedeemKeyModal(discord.ui.Modal, title="🔑 Canjear Clave"):
    key_input = discord.ui.TextInput(
        label="Ingresa tu clave de acceso",
        placeholder="XXXX-XXXX-XXXX-XXXX-XXXX",
        style=discord.TextStyle.short,
        required=True,
        max_length=24
    )

    async def on_submit(self, interaction: discord.Interaction):
        key = str(self.key_input.value).strip().upper()

        print(f"\n" + "="*50)
        print(f"🔑 USUARIO INTENTANDO CANJEAR CLAVE")
        print(f"📱 Usuario: {interaction.user} (ID: {interaction.user.id})")
        print(f"🔑 Clave ingresada: {key}")
        print(f"📊 Total claves en BD: {len(KEY_DATABASE)}")
        print("="*50)

        # DEBUG: Mostrar estado de todas las claves
        print("🔍 ESTADO ACTUAL DE CLAVES:")
        for k, data in list(KEY_DATABASE.items())[:10]:  # Mostrar solo primeras 10
            status = data.get('status', 'NO-STATUS')
            user = data.get('user_id', 'NO-USER')
            print(f"   {k} -> Estado: {status}, User: {user}")

        if len(KEY_DATABASE) > 10:
            print(f"   ... y {len(KEY_DATABASE) - 10} más")

        # VERIFICAR SI LA CLAVE EXISTE
        if key not in KEY_DATABASE:
            print(f"❌ CLAVE NO ENCONTRADA: {key}")

            # Mostrar claves disponibles para ayudar al usuario
            available_keys = [k for k, d in KEY_DATABASE.items() if d.get('status') == 'unused']
            print(f"🟡 Claves disponibles: {len(available_keys)}")
            if available_keys:
                print(f"🟡 Ejemplos: {available_keys[:3]}")

            embed = discord.Embed(
                title="❌ Clave Inválida",
                description="La clave que ingresaste no existe en nuestro sistema.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="¿Qué hacer?",
                value="• Verifica que la clave sea correcta\n• Asegúrate de no tener espacios extras\n• Contacta al soporte si el problema persiste",
                inline=False
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        key_data = KEY_DATABASE[key]
        current_status = key_data.get('status', 'NO-STATUS')
        current_user = key_data.get('user_id', 'NO-USER')

        print(f"📋 DATOS DE LA CLAVE:")
        print(f"   Estado: {current_status}")
        print(f"   Usuario actual: {current_user}")
        print(f"   Expira: {key_data.get('expires_at')}")

        # VERIFICAR ESTADO DE LA CLAVE
        if current_status != 'unused':
            print(f"❌ CLAVE YA UTILIZADA - Estado: {current_status}")

            embed = discord.Embed(
                title="❌ Clave Ya Utilizada",
                description="Esta clave ya ha sido canjeada anteriormente.",
                color=discord.Color.orange()
            )

            if current_status == 'active':
                embed.add_field(
                    name="Estado Actual",
                    value="🟢 **ACTIVA** - Ya está en uso por otro usuario",
                    inline=False
                )
            elif current_status == 'expired':
                embed.add_field(
                    name="Estado Actual", 
                    value="🔴 **EXPIRADA** - El tiempo de acceso ha terminado",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Estado Actual",
                    value=f"❓ **{current_status.upper()}** - Estado desconocido",
                    inline=False
                )

            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # VERIFICAR SI EL USUARIO YA TIENE CLAVE ACTIVA
        user_active_keys = []
        for existing_key, data in KEY_DATABASE.items():
            if data.get('user_id') == interaction.user.id and data.get('status') == 'active':
                user_active_keys.append(existing_key)

        if user_active_keys:
            print(f"❌ USUARIO YA TIENE CLAVE ACTIVA: {user_active_keys}")

            embed = discord.Embed(
                title="❌ Ya Tienes una Clave Activa",
                description=f"Actualmente tienes la clave: `{user_active_keys[0]}`",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="¿Qué hacer?",
                value="• Usa la clave que ya tienes activa\n• O contacta soporte para cambiar de clave",
                inline=False
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # ✅ TODO CORRECTO - ACTIVAR LA CLAVE
        try:
            print(f"🎯 ACTIVANDO CLAVE PARA USUARIO...")

            # Actualizar datos de la clave
            key_data.update({
                'status': 'active',
                'user_id': interaction.user.id,
                'username': str(interaction.user),
                'redeemed_at': datetime.datetime.now(datetime.timezone.utc)
            })

            # Si no tiene fecha de expiración, agregar 30 días por defecto
            if not key_data.get('expires_at'):
                key_data['expires_at'] = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
                print(f"📅 Fecha de expiración establecida: {key_data['expires_at']}")

            # Guardar cambios
            save_database()

            print(f"🎉 CLAVE ACTIVADA EXITOSAMENTE!")
            print(f"   Clave: {key}")
            print(f"   Usuario: {interaction.user.id}")
            print(f"   Nuevo estado: {KEY_DATABASE[key].get('status')}")

            # Embed de éxito
            embed = discord.Embed(
                title="🎉 ¡Clave Canjeada con Éxito!",
                description="Tu acceso a **JOSE018 joiner** ha sido activado correctamente.",
                color=discord.Color.green()
            )
            embed.add_field(
                name="🔑 Tu Clave",
                value=f"||`{key}`||",
                inline=False
            )
            embed.add_field(
                name="👤 Usuario",
                value=interaction.user.mention,
                inline=True
            )
            embed.add_field(
                name="🕒 Canjeada",
                value=f"<t:{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}:R>",
                inline=True
            )

            if key_data.get('expires_at'):
                embed.add_field(
                    name="📅 Expira",
                    value=f"<t:{int(key_data['expires_at'].timestamp())}:R>",
                    inline=True
                )

            embed.add_field(
                name="🚀 Siguientes Pasos",
                value="• Usa **Get Script** para obtener tu script\n• Usa **Get Role** para tu rol especial\n• ¡Disfruta de JOSE018 joiner!",
                inline=False
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"❌ ERROR CRÍTICO ACTIVANDO CLAVE: {e}")
            embed = discord.Embed(
                title="❌ Error Interno",
                description="Ha ocurrido un error al activar tu clave. Por favor contacta al soporte.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class PanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def get_user_key_data(self, user_id: int):
        """Encuentra la clave activa de un usuario"""
        for key, data in KEY_DATABASE.items():
            if data.get('user_id') == user_id and data.get('status') == 'active':
                return key, data
        return None, None

    @discord.ui.button(label="Redeem Key", style=discord.ButtonStyle.success, emoji="🔑", custom_id="panel_redeem", row=0)
    async def redeem_key(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RedeemKeyModal())

    @discord.ui.button(label="Get Script", style=discord.ButtonStyle.primary, emoji="📦", custom_id="panel_getscript", row=0)
    async def get_script(self, interaction: discord.Interaction, button: discord.ui.Button):
        key, key_data = self.get_user_key_data(interaction.user.id)

        if not key:
            embed = discord.Embed(
                title="❌ Clave No Encontrada",
                description="No tienes una clave activa. Usa **Redeem Key** primero.",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # Verificar expiración
        if key_data.get('expires_at') and datetime.datetime.now(datetime.timezone.utc) > key_data['expires_at']:
            embed = discord.Embed(
                title="❌ Clave Expirada",
                description="Tu clave ha expirado. Contacta al soporte para renovarla.",
                color=discord.Color.orange()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        script_content = f'''_G.JOSE018Key = "{key}"
loadstring(game:HttpGet("https://pastefy.app/asZ19JJc/raw"))()'''

        embed = discord.Embed(
            title="📦 Script Oficial JOSE018 joiner",
            description="Aquí tienes tu script personalizado:",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📝 Código",
            value=f"```lua\n{script_content}\n```",
            inline=False
        )
        embed.add_field(
            name="⚡ Cómo Usar",
            value="1. **Copia TODO el código**\n2. **Pégalo en tu ejecutor**\n3. **¡Disfruta de jose018joiner!**",
            inline=False
        )
        embed.add_field(
            name="⚠️ Advertencia",
            value="**NO COMPARTAS** este código con nadie. Es personal e intransferible.",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Get Role", style=discord.ButtonStyle.primary, emoji="👤", custom_id="panel_getrole", row=1)
    async def get_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not ROL_COMPRADOR_ID:
            embed = discord.Embed(
                title="❌ Error de Configuración",
                description="El rol de comprador no está configurado.",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        key, key_data = self.get_user_key_data(interaction.user.id)
        if not key:
            embed = discord.Embed(
                title="❌ Clave Requerida",
                description="Necesitas una clave activa para obtener el rol.",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        role = interaction.guild.get_role(ROL_COMPRADOR_ID)
        if not role:
            embed = discord.Embed(
                title="❌ Rol No Encontrado",
                description="No se pudo encontrar el rol de comprador.",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if role in interaction.user.roles:
            embed = discord.Embed(
                title="✅ Rol Ya Asignado",
                description=f"Ya tienes el rol {role.mention}.",
                color=discord.Color.blue()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            await interaction.user.add_roles(role, reason=f"Clave canjeada: {key}")
            embed = discord.Embed(
                title="🎉 ¡Rol Asignado!",
                description=f"Se te ha asignado el rol {role.mention} correctamente.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Error de Permisos",
                description="No tengo permisos para asignar roles.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Error al asignar rol: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Reset HWID", style=discord.ButtonStyle.secondary, emoji="⚙️", custom_id="panel_resethwid", row=1)
    async def reset_hwid(self, interaction: discord.Interaction, button: discord.ui.Button):
        key, key_data = self.get_user_key_data(interaction.user.id)
        if not key:
            embed = discord.Embed(
                title="❌ Clave No Encontrada",
                description="No tienes una clave activa.",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            # Resetear HWID en la base de datos local
            key_data['hwid'] = None

            # Resetear HWID en el servidor de autenticación
            response = requests.post(f"{API_URL}/reset-hwid", json={"key": key}, timeout=10)

            save_database()

            if response.status_code == 200 and response.json().get('success'):
                embed = discord.Embed(
                    title="⚙️ HWID Reseteado",
                    description="El HWID ha sido reseteado correctamente. Ahora puedes usar el script en otro dispositivo.",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="⚠️ HWID Reseteado (Local)",
                    description="HWID reseteado en base local, pero hubo un error con el servidor de autenticación.",
                    color=discord.Color.orange()
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Error al resetear HWID: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Get Stats", style=discord.ButtonStyle.secondary, emoji="📊", custom_id="panel_stats", row=2)
    async def get_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        key, key_data = self.get_user_key_data(interaction.user.id)
        if not key:
            embed = discord.Embed(
                title="❌ Sin Clave Activa",
                description="No tienes ninguna clave activa.",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        embed = discord.Embed(
            title="📊 Estado de tu Clave",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="🔑 Clave",
            value=f"||`{key}`||",
            inline=False
        )

        if key_data.get('redeemed_at'):
            embed.add_field(
                name="🕒 Canjeada",
                value=f"<t:{int(key_data['redeemed_at'].timestamp())}:R>",
                inline=True
            )

        if key_data.get('expires_at'):
            if datetime.datetime.now(datetime.timezone.utc) > key_data['expires_at']:
                embed.add_field(
                    name="🔴 Estado",
                    value="Expirada",
                    inline=True
                )
            else:
                embed.add_field(
                    name="🟢 Expira",
                    value=f"<t:{int(key_data['expires_at'].timestamp())}:R>",
                    inline=True
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)

# =======================================================
# CONFIGURACIÓN DEL BOT
# =======================================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

def is_owner():
    """Verificador para comandos de dueño"""
    async def predicate(interaction: discord.Interaction):
        return interaction.user.id in [OWNER_USER_ID, SECOND_OWNER_ID]
    return discord.app_commands.check(predicate)

@bot.event
async def on_ready():
    print(f"\n" + "="*60)
    print(f"✅ BOT CONECTADO EXITOSAMENTE")
    print(f"🤖 Nombre: {bot.user.name}")
    print(f"🆔 ID: {bot.user.id}")
    print(f"📊 Claves en BD: {len(KEY_DATABASE)}")
    print(f"🛡️ Dueños: {OWNER_USER_ID}, {SECOND_OWNER_ID}")
    print(f"🏠 Servidor: {GUILD_ID}")
    print(f"👤 Rol Comprador: {ROL_COMPRADOR_ID}")
    print(f"🌐 API URL: {API_URL}")
    print("="*60)

    # Mostrar estadísticas de claves
    unused = len([k for k, d in KEY_DATABASE.items() if d.get('status') == 'unused'])
    active = len([k for k, d in KEY_DATABASE.items() if d.get('status') == 'active'])
    expired = len([k for k, d in KEY_DATABASE.items() if d.get('status') == 'expired'])

    print(f"📈 ESTADÍSTICAS DE CLAVES:")
    print(f"   🆕 Sin usar: {unused}")
    print(f"   ✅ Activas: {active}") 
    print(f"   ❌ Expiradas: {expired}")
    print(f"   📊 Total: {len(KEY_DATABASE)}")

    # Iniciar tareas
    key_expiry_check.start()
    print("🔄 Tareas de verificación iniciadas")

@tasks.loop(hours=1)
async def key_expiry_check():
    """Verifica y expira claves vencidas cada hora"""
    try:
        now = datetime.datetime.now(datetime.timezone.utc)
        guild = bot.get_guild(GUILD_ID)

        if not guild or not ROL_COMPRADOR_ID:
            return

        keys_to_expire = []
        for key, data in KEY_DATABASE.items():
            if (data.get('status') == 'active' and 
                data.get('expires_at') and 
                now > data['expires_at']):
                keys_to_expire.append(key)

        if keys_to_expire:
            print(f"🕐 Expiradas {len(keys_to_expire)} claves")
            role = guild.get_role(ROL_COMPRADOR_ID)

            for key in keys_to_expire:
                user_id = KEY_DATABASE[key].get('user_id')
                KEY_DATABASE[key]['status'] = 'expired'

                if user_id and role:
                    try:
                        member = await guild.fetch_member(user_id)
                        if role in member.roles:
                            await member.remove_roles(role, reason="Clave expirada")
                            print(f"👤 Rol removido de {member}")
                    except Exception as e:
                        print(f"⚠️ Error removiendo rol de {user_id}: {e}")

            save_database()

    except Exception as e:
        print(f"❌ Error en verificación de expiración: {e}")

# =======================================================
# COMANDOS DE DUEÑO
# =======================================================

@bot.tree.command(name="panel", description="[OWNER] Despliega el panel de control")
@is_owner()
async def panel(interaction: discord.Interaction):
    """Despliega el panel de control para usuarios"""
    active_keys = len([k for k, d in KEY_DATABASE.items() if d.get('status') == 'active'])
    total_keys = len(KEY_DATABASE)
    unused_keys = len([k for k, d in KEY_DATABASE.items() if d.get('status') == 'unused'])

    embed = discord.Embed(
        title="🎮 PANEL DE CONTROL - JOSE018",
        description=(
            "**Bienvenido al panel de gestión para compradores**\n\n"
            "Usa los botones below para gestionar tu acceso a JOSE018."
        ),
        color=discord.Color.gold()
    )

    embed.add_field(
        name="📊 Estadísticas del Sistema",
        value=(
            f"• **Claves Activas:** `{active_keys}`\n"
            f"• **Claves Disponibles:** `{unused_keys}`\n" 
            f"• **Claves Totales:** `{total_keys}`"
        ),
        inline=False
    )

    embed.add_field(
        name="🔑 Gestión de Claves",
        value=(
            "**Redeem Key** - Canjear tu clave de acceso\n"
            "**Get Script** - Obtener script personalizado\n"
            "**Get Role** - Obtener rol de comprador\n"
            "**Reset HWID** - Resetear dispositivo\n"
            "**Get Stats** - Ver estado de tu clave"
        ),
        inline=False
    )

    embed.set_footer(text=f"Panel desplegado por {interaction.user.name}")

    await interaction.response.send_message(embed=embed, view=PanelView())

@bot.tree.command(name="generate", description="[OWNER] Genera nuevas claves de acceso")
@is_owner()
@discord.app_commands.describe(
    cantidad="Número de claves a generar",
    dias="Duración en días de las claves"
)
async def generate(interaction: discord.Interaction, cantidad: int, dias: int):
    """Genera nuevas claves de acceso"""
    await interaction.response.defer(ephemeral=True)

    if cantidad <= 0 or dias <= 0:
        embed = discord.Embed(
            title="❌ Parámetros Inválidos",
            description="La cantidad y días deben ser números positivos.",
            color=discord.Color.red()
        )
        return await interaction.followup.send(embed=embed, ephemeral=True)

    if cantidad > 1000:
        embed = discord.Embed(
            title="❌ Límite Excedido",
            description="No puedes generar más de 1000 claves a la vez.",
            color=discord.Color.red()
        )
        return await interaction.followup.send(embed=embed, ephemeral=True)

    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=dias)
    generated_keys = []

    print(f"🔑 GENERANDO {cantidad} CLAVES POR {dias} DÍAS...")

    for i in range(cantidad):
        # Generar clave en formato XXXX-XXXX-XXXX-XXXX-XXXX
        raw_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
        key = '-'.join([raw_key[i:i+4] for i in range(0, 20, 4)])

        # Crear entrada en la base de datos
        KEY_DATABASE[key] = {
            'status': 'unused',
            'expires_at': expires_at,
            'user_id': None,
            'hwid': None,
            'redeemed_at': None,
            'username': None,
            'created_at': datetime.datetime.now(datetime.timezone.utc)
        }

        generated_keys.append(key)
        print(f"   {i+1}. {key}")

    # Guardar base de datos
    save_database()

    print(f"✅ {cantidad} CLAVES GENERADAS EXITOSAMENTE")

    # Preparar respuesta
    key_string = "\n".join(generated_keys)

    if cantidad > 10:
        # Si son muchas claves, enviar como archivo
        file_content = io.StringIO(key_string)
        text_file = discord.File(file_content, filename=f"neonhub_keys_{dias}dias.txt")

        embed = discord.Embed(
            title="🔑 Claves Generadas",
            description=(
                f"Se generaron **{cantidad}** claves de acceso válidas por **{dias} días**.\n"
                f"📅 **Expiran:** <t:{int(expires_at.timestamp())}:R>\n\n"
                f"Las claves se han guardado en el archivo adjunto."
            ),
            color=discord.Color.green()
        )

        await interaction.followup.send(embed=embed, file=text_file, ephemeral=True)

    else:
        # Si son pocas claves, mostrar en embed
        embed = discord.Embed(
            title="🔑 Claves Generadas",
            description=(
                f"Se generaron **{cantidad}** claves de acceso válidas por **{dias} días**.\n"
                f"📅 **Expiran:** <t:{int(expires_at.timestamp())}:R>"
            ),
            color=discord.Color.green()
        )

        embed.add_field(
            name="Claves Generadas",
            value=f"```\n{key_string}\n```",
            inline=False
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="debug_keys", description="[OWNER] Muestra información de debug de las claves")
@is_owner()
async def debug_keys(interaction: discord.Interaction):
    """Comando de debug para ver el estado de la base de datos"""
    await interaction.response.defer(ephemeral=True)

    if not KEY_DATABASE:
        embed = discord.Embed(
            title="📊 Debug - Base de Datos",
            description="La base de datos está vacía.",
            color=discord.Color.orange()
        )
        return await interaction.followup.send(embed=embed, ephemeral=True)

    # Estadísticas
    total = len(KEY_DATABASE)
    unused = len([k for k, d in KEY_DATABASE.items() if d.get('status') == 'unused'])
    active = len([k for k, d in KEY_DATABASE.items() if d.get('status') == 'active'])
    expired = len([k for k, d in KEY_DATABASE.items() if d.get('status') == 'expired'])

    embed = discord.Embed(
        title="🔧 Debug - Base de Datos",
        color=discord.Color.blue()
    )

    embed.add_field(name="📊 Estadísticas", value=f"**Total:** {total}\n**Sin usar:** {unused}\n**Activas:** {active}\n**Expiradas:** {expired}", inline=False)

    # Ejemplos de claves sin usar
    unused_examples = [k for k, d in KEY_DATABASE.items() if d.get('status') == 'unused'][:5]
    if unused_examples:
        embed.add_field(
            name="🆕 Claves Sin Usar (Ejemplos)",
            value="\n".join([f"`{k}`" for k in unused_examples]),
            inline=False
        )

    # Ejemplos de claves activas
    active_examples = []
    for k, d in list(KEY_DATABASE.items()):
        if d.get('status') == 'active':
            user_id = d.get('user_id', 'N/A')
            username = d.get('username', 'N/A')
            active_examples.append(f"`{k}` - User: {user_id} ({username})")
            if len(active_examples) >= 3:
                break

    if active_examples:
        embed.add_field(
            name="✅ Claves Activas (Ejemplos)",
            value="\n".join(active_examples),
            inline=False
        )

    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="stats", description="[OWNER] Muestra estadísticas del sistema")
@is_owner()
async def stats(interaction: discord.Interaction):
    """Muestra estadísticas completas del sistema"""
    total_keys = len(KEY_DATABASE)
    unused_keys = len([k for k, d in KEY_DATABASE.items() if d.get('status') == 'unused'])
    active_keys = len([k for k, d in KEY_DATABASE.items() if d.get('status') == 'active'])
    expired_keys = len([k for k, d in KEY_DATABASE.items() if d.get('status') == 'expired'])

    embed = discord.Embed(
        title="📊 Estadísticas del Sistema - NeonHub Premium",
        color=discord.Color.purple()
    )

    embed.add_field(name="🔑 Total de Claves", value=f"`{total_keys}`", inline=True)
    embed.add_field(name="🆕 Sin Usar", value=f"`{unused_keys}`", inline=True)
    embed.add_field(name="✅ Activas", value=f"`{active_keys}`", inline=True)
    embed.add_field(name="❌ Expiradas", value=f"`{expired_keys}`", inline=True)

    # Porcentajes
    if total_keys > 0:
        unused_percent = (unused_keys / total_keys) * 100
        active_percent = (active_keys / total_keys) * 100
        expired_percent = (expired_keys / total_keys) * 100

        embed.add_field(
            name="📈 Porcentajes",
            value=(
                f"**Sin usar:** {unused_percent:.1f}%\n"
                f"**Activas:** {active_percent:.1f}%\n"
                f"**Expiradas:** {expired_percent:.1f}%"
            ),
            inline=False
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="fix_database", description="[OWNER] Repara posibles problemas en la base de datos")
@is_owner()
async def fix_database(interaction: discord.Interaction):
    """Repara problemas comunes en la base de datos"""
    await interaction.response.defer(ephemeral=True)

    fixes_applied = 0
    problems_found = []

    # Verificar y reparar cada clave
    for key, data in KEY_DATABASE.items():
        # Reparar: Si no tiene status, establecer como 'unused'
        if 'status' not in data:
            data['status'] = 'unused'
            fixes_applied += 1
            problems_found.append(f"Clave `{key}`: Agregado status 'unused'")

        # Reparar: Si no tiene created_at, agregarlo
        if 'created_at' not in data:
            data['created_at'] = datetime.datetime.now(datetime.timezone.utc)
            fixes_applied += 1
            problems_found.append(f"Clave `{key}`: Agregado created_at")

    if fixes_applied > 0:
        save_database()

        embed = discord.Embed(
            title="🔧 Base de Datos Reparada",
            description=f"Se aplicaron **{fixes_applied}** reparaciones.",
            color=discord.Color.green()
        )

        # Mostrar primeras 5 reparaciones
        if problems_found:
            embed.add_field(
                name="📝 Reparaciones Aplicadas",
                value="\n".join(problems_found[:5]) + 
                     (f"\n... y {len(problems_found) - 5} más" if len(problems_found) > 5 else ""),
                inline=False
            )

    else:
        embed = discord.Embed(
            title="✅ Base de Datos OK",
            description="No se encontraron problemas que reparar.",
            color=discord.Color.blue()
        )

    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.event
async def setup_hook():
    """Configuración inicial del bot"""
    # Registrar vistas persistentes
    bot.add_view(PanelView())
    print("👀 Vistas persistentes registradas")

    # Sincronizar comandos
    if GUILD_ID:
        try:
            guild = discord.Object(id=GUILD_ID)
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
            print("🔄 Comandos sincronizados con el servidor")
        except Exception as e:
            print(f"❌ Error sincronizando comandos: {e}")

# =======================================================
# INICIALIZACIÓN
# =======================================================

# Mantener el bot activo
keep_alive()

# Iniciar el bot
if __name__ == "__main__":
    print("🚀 INICIANDO BOT JOSE018 joiner...")

    # Verificar variables esenciales
    required_vars = {
        "DISCORD_TOKEN": DISCORD_TOKEN,
        "GUILD_ID": GUILD_ID,
        "OWNER_USER_ID": OWNER_USER_ID,
        "ROL_COMPRADOR_ID": ROL_COMPRADOR_ID
    }

    missing_vars = [var for var, value in required_vars.items() if not value]

    if missing_vars:
        print(f"❌ ERROR: Faltan variables esenciales en .env:")
        for var in missing_vars:
            print(f"   - {var}")
        print("💡 Asegúrate de que tu archivo .env tenga todas las variables requeridas.")
    else:
        print("✅ Todas las variables de entorno están configuradas correctamente.")
        try:
            bot.run(DISCORD_TOKEN)
        except Exception as e:
            print(f"❌ Error iniciando el bot: {e}")
