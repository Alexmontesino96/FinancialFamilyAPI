# Configuración del Repositorio en GitHub

Para subir tu código a GitHub, sigue estos pasos:

## 1. Crear un nuevo repositorio en GitHub

1. Ve a [GitHub](https://github.com/) e inicia sesión en tu cuenta.
2. Haz clic en el botón "+" en la esquina superior derecha y selecciona "New repository".
3. Nombra tu repositorio como "FinancialFamilyAPI".
4. (Opcional) Añade una descripción como "API para gestionar finanzas familiares compartidas".
5. Deja el repositorio como público o selecciona privado según tus preferencias.
6. NO inicialices el repositorio con un README, .gitignore o licencia, ya que ya tienes estos archivos localmente.
7. Haz clic en "Create repository".

## 2. Subir tu código al repositorio

Una vez creado el repositorio, GitHub te mostrará instrucciones. Sigue las instrucciones para un repositorio existente:

```bash
# Ya has ejecutado estos comandos
# git init
# git add .
# git commit -m "Versión inicial de FinancialFamilyAPI con soporte para PostgreSQL y pruebas"

# Configura el repositorio remoto (reemplaza USERNAME por tu nombre de usuario de GitHub)
git remote add origin https://github.com/USERNAME/FinancialFamilyAPI.git

# Sube tu código al repositorio
git push -u origin main
```

## 3. Autenticación

Si es la primera vez que usas Git con GitHub, es posible que te solicite autenticación. Puedes usar:

- Tu nombre de usuario y contraseña de GitHub (si tienes habilitada la autenticación de dos factores, necesitarás un token de acceso personal).
- Un token de acceso personal: puedes generarlo en GitHub en Settings > Developer settings > Personal access tokens.
- SSH: si tienes configurada una clave SSH con GitHub.

## 4. Verificar

Una vez completado el push, actualiza la página de tu repositorio en GitHub y deberías ver todos tus archivos subidos correctamente. 