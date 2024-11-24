from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import requests
import time

binary_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

driver_path = r"C:\Users\Nouh\Desktop\Scrapping\chromedriver.exe"

options = Options()
options.binary_location = binary_path

service = Service(driver_path)

driver = webdriver.Chrome(service=service, options=options)

driver.get('https://www.upv.es')

with open('dni.txt','r') as dni_raw:
    dni = dni_raw.read()

with open('contra.txt','r') as contra_raw:
    contra = contra_raw.read()
driver.get('https://intranet.upv.es/pls/soalu/est_intranet.NI_Portal_n?p_idioma=c')
time.sleep(1)
escribir_dni = driver.find_element(By.NAME, 'dni')
escribir_dni.send_keys(dni)
escribir_contra = driver.find_element(By.NAME, 'clau')
escribir_contra.send_keys(contra)
escribir_contra.send_keys(Keys.ENTER)
time.sleep(5)
driver.get('https://intranet.upv.es/pls/soalu/sic_depact.HSemActividades?p_campus=V&p_tipoact=6799&p_codacti=21549&p_vista=intranet&p_idioma=c&p_solo_matricula_sn=&p_anc=filtro_actividad')

request = driver.page_source
soup = BeautifulSoup(request,'html.parser')
enlaces = soup.find_all('a', class_='upv_enlacelista')

urls_finales = []
horas_interesantes = ['009','024','039','054','069','010','025','040','055','070']
contador = 0

"""
for enlace in enlaces:
    url = enlace.get('href')
    texto = enlace.get_text(separator=" ").strip()
    print(f'{texto}: {url} ')


for enlace in enlaces:
    url = enlace.get('href')
    texto = enlace.get_text(separator=" ").strip()
    for sesion in horas_interesantes:
        string = 'MUS' + sesion
        if string in texto:
            urls_finales.append(url)
            print(f'{marcador_visual}\n{texto}: {url}\n{marcador_visual}')
            break
    #print(f'{texto}: {url}')
    marcador_visual = '*' 50
    
"""

botones_reserva = driver.find_elements(By.CLASS_NAME, 'upv_enlacelista')

for boton in botones_reserva:
    print(boton.get_attribute('href'))

botones_reserva = driver.find_elements(By.CLASS_NAME, 'upv_enlacelista')
urls_reserva = []
marcador_visual = '*' * 50
for boton in botones_reserva:
    url = boton.get_attribute('href')
    texto_enlace = boton.text.strip()
    texto_enlace = texto_enlace[:6]
    for sesion in horas_interesantes:
        string = 'MUS' + sesion
        if string in texto_enlace:
            urls_reserva.append(url)
            print(f'{marcador_visual}\n{texto_enlace}: {url}\n{marcador_visual}')
for url in urls_reserva:
    driver.get(url)  
    time.sleep(1)