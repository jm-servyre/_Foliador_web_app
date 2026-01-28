# 📄 Foliador de PDF Web - Enterprise Solution (v3.2)

Sistema profesional para la numeración automatizada de documentos PDF. Diseñado para alta disponibilidad en redes locales (LAN) y despliegue ágil en plataformas Cloud.

---

## 🚀 Despliegue en la Nube (Render.com)
Para poner tu página en línea ahora mismo, sigue estos pasos:

1. **Crear cuenta:** Regístrate en [Render.com](https://render.com) usando tu cuenta de GitHub.
2. **Nuevo servicio:** Haz clic en `New +` > `Web Service`.
3. **Conectar Repo:** Selecciona tu repositorio público.
4. **Configuración Técnica:**
   - **Runtime:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. **Listo:** Render te dará una URL pública (ej. `mi-foliador.onrender.com`).

---

## 🌐 Configuración de Red Local (Oficina)
Si prefieres usarlo de forma interna sin Internet:

1. **Ejecución:** En la terminal corre `python app.py`.
2. **Acceso:** Desde cualquier PC en la red entra a `http://192.168.2.123:5000`.
3. **Requisito:** El Firewall de Windows debe permitir el puerto **5000** y la red debe ser **Privada**.

---

## 🛠️ Solución de Problemas (Troubleshooting)

| Error | Causa | Solución |
| :--- | :--- | :--- |
| **VCRUNTIME140_1.dll** | Falta runtime de C++. | Instalar el [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe). |
| **Página no carga en LAN** | Firewall o Red Pública. | Cambiar red a **Privada** y abrir puerto 5000. |
| **Error en Render** | Falta Procfile o requirements. | Verificar que ambos archivos estén en la raíz del repositorio. |

---
*Documentación técnica por Jorge Meneses - 2026*