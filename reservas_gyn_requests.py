import requests
from bs4 import BeautifulSoup
import time

# URLs
login_url = "https://intranet.upv.es/pls/soalu/est_intranet.NI_Portal_n?p_idioma=c"
login_params = "https://intranet.upv.es/pls/soalu/est_aute.intraalucomp"
#gym_url = "https://intranet.upv.es/pls/soalu/sic_depact.HSemActividades?p_campus=V&p_tipoact=6799&p_codacti=21549&p_vista=intranet&p_idioma=c&p_solo_matricula_sn=&p_anc=filtro_actividad"
gym_url = 'https://intranet.upv.es/pls/soalu/sic_depact.HSemActividades?p_campus=V&p_codacti=21549&p_vista=intranet&p_idioma=c&p_tipoact=6799&p_solo_matricula_sn=&p_anc=bloque_inscritas'
# Leer credenciales
with open('dni.txt', 'r') as dni_raw:
    dni = dni_raw.read()

with open('contra.txt', 'r') as contra_raw:
    contra = contra_raw.read()
# Crear una sesión para manejar cookies y autenticación
session = requests.Session()
session
# Paso 1: Hacer login
login_data = {
    'dni': dni,
    'clau': contra
}

response = session.post(login_params, data=login_data)
response
response = session.get(gym_url, allow_redirects=True)

if response.status_code == 200:
    print("Acceso exitoso al sistema de reservas.")
else:
    print("Error al acceder al sistema de reservas.")
soup = BeautifulSoup(response.text, 'html.parser')
print(soup.prettify())

enlaces = soup.find_all('a', class_='upv_enlacelista')  # Ajusta la clase según lo que veas en el HTML
horas_interesantes = ['009', '024', '039', '054', '069', '010', '025', '040', '055', '070']
urls_reserva = []
enlaces
for enlace in enlaces:
    url = enlace.get('href')
    texto = enlace.get_text(separator=" ").strip()
    for sesion in horas_interesantes:
        string = 'MUS' + sesion
        if string in texto:
            urls_reserva.append(f"https://intranet.upv.es/pls/soalu/{url}")  # Completar con el dominio si es necesario
            horas_interesantes.remove(sesion)
            print(f"Encontrado: {texto} - https://intranet.upv.es/pls/soalu/{url}")
            break
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "es-ES,es;q=0.9",
    "Connection": "keep-alive",
    "Cookie": "JS=1; T=foto1; AMFParams=dummy,false,false,false,false,true,windows,nc,chrome,123.0.0.0; AMFDetect=true; iacclarge=; UPV_DEBUG=,iacclarge; accesible=HighContrast; UPV_IDIOMA=es; UPV_TRANS_RECO_CARGA_ACTIVIDADES=202407180930; lhc_per={}; _ga_VMJD28FTH6=GS1.1.1726307117.3.1.1726307138.0.0.0; _ga_82DFBN6965=GS1.1.1729790722.13.1.1729790728.0.0.0; _ga=GA1.1.1328595174.1729439601; _ga_FH0S6SQPXT=GS1.1.1732451605.38.0.1732451606.0.0.0; TDp=746BB4B5289290B7B9E647A19A3CEA67",
    "Host": "intranet.upv.es",
    "Referer": "https://intranet.upv.es/pls/soalu/sic_depact.HSemActividades?p_campus=V&p_codacti=21549&p_vista=intranet&p_idioma=c&p_tipoact=6799&p_solo_matricula_sn=&p_anc=bloque_inscritas",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 OPR/114.0.0.0",
    "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Opera GX";v="114"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}
cookies = session.cookies.get_dict()
print(f"Cookies activas: {cookies}")
intentos = 1
while urls_reserva:
    if not urls_reserva:
         break
    print(f'Intento Nº{intentos}:')
    try:
        for url in urls_reserva:
                reserva_response = session.get(url, headers=headers, cookies=cookies)
                if reserva_response.status_code == 200:
                    print(f"Reservado: {url}")
                    urls_reserva.remove(url)
    except:
        if not urls_reserva:
             break
        print(f"Error al reservar: {url}")
        intentos += 1
        time.sleep(5)