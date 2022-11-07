# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from email import message
from pickle import FALSE
import string
from tkinter import N
from tokenize import Double
from typing import Any, Text, Dict, List
from numpy import double, integer
#
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from datetime import datetime
import json
import random
import requests
from flask import jsonify

from sqlalchemy import case, false, true

#
#

def readArchivo(dire)-> dict:
        with open(dire,"r") as archivo:
            diccionario = json.loads(archivo.read()) 
            archivo.close()
        return diccionario

def writeArchivo(dire,diccionario):
        with open(dire,"w") as archivo:
            json.dump(diccionario,archivo)
            archivo.close()

api_endpoint_set_vector = "http://181.94.129.186:8088/dispatcher/set-vector"
api_endpoint_get_vector = "http://181.94.129.186:8088/dispatcher/get-vector"
diccionarioParticipantes = ""
#Variables utilizadas para guardar los valores
pregunta_actual = 0
valor_riesgo = 0
valor_optimismo = 0
valor_adaptabilidad = 0
habilidades = []
lenguajes = []
preguntas_totales = 18

def existeParticipante(nombre_participante) -> bool:
    response = requests.get(url=api_endpoint_get_vector).text
    #print("response: " + response)
    diccionarioParticipantes = json.loads(response)
    for participante in diccionarioParticipantes:
        if (participante["nickname"] == nombre_participante):
            return True
    return False

def crearVector(riesgo, optimismo, adaptabilidad, habilidades, lenguajes):
    vector = {}
    vector["riesgo"] = riesgo
    vector["optimismo"] = optimismo
    vector["adaptabilidad"] = adaptabilidad
    vector["habilidades"] = habilidades
    vector["lenguajes"] = lenguajes
    return vector

def altaValores(nombre_partipante):
    global valor_riesgo, valor_optimismo, valor_adaptabilidad, habilidades, lenguajes
    data = {}
    data ["agilebotId"] = nombre_partipante
    data ["vector"] = crearVector(round(valor_riesgo/3), round(valor_optimismo/3), round(valor_adaptabilidad/3), habilidades, lenguajes) #Casteo el valor a entero y lo divido por 3 al ser la cantidad de preguntas
    r = requests.post(url=api_endpoint_set_vector, json=data)
    print(data)
    #response = requests.get(url=api_endpoint_get_vector).text
    #print("response: " + response)

def darAlta(nombre_participante) -> bool:
    global pregunta_actual, preguntas_totales
    if (pregunta_actual == preguntas_totales): #Chequeo si se realizaron de forma correcta todas la preguntas para asi dar de alta
        altaValores(nombre_participante)
        return true
    else:
        return false

class ActionGuardarNombre(Action):

    def name(self) -> Text:
        return "guardar_nombre"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        nombre_partipante = next (tracker.get_latest_entity_values("participante"),None)
        message = ""
        if (nombre_partipante != None):
            #Reinicio las varibles globales
            global pregunta_actual, valor_riesgo, valor_optimismo, valor_adaptabilidad, habilidades, lenguajes
            pregunta_actual = 0
            valor_riesgo = 0
            valor_optimismo = 0
            valor_adaptabilidad = 0
            habilidades = []
            lenguajes = []
            if(existeParticipante(nombre_partipante)):
                message = "Hola, vamos a realizar una prueba de aptitud para ver lo que votarias ante ciertas tareas. Ademas, te voy a realizar algunas consultas para determinar los conocimientos que tenes actualmente"
                dispatcher.utter_message(text=message)
                message = "En las proximas preguntas debes votar con valores del 0 al 5"
                dispatcher.utter_message(text=message)
                message = "Que tan comodo te sentis ante una situacion desconocida?"
                dispatcher.utter_message(text=message)
            else:
                message = "El nombre no corresponde a un AgileBot perteneciente al mundo"
                dispatcher.utter_message(text=message)
        else:
            message = "No se puede reconocer el nombre del AgileBot"
            dispatcher.utter_message(text=message)
        return [SlotSet("participante",str(nombre_partipante))]

class ActionGuardarValorRespuesta(Action):
    def name(self) -> Text:
        return "guardar_valor_respuesta"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global valor_riesgo, valor_optimismo, valor_adaptabilidad, habilidades, lenguajes, pregunta_actual #Declaro las variables globales a utilizar
        valor_respuesta = next (tracker.get_latest_entity_values("valor_respuesta"),None)
        message = "Error"
        if (valor_respuesta != None):
            valor_respuesta = int(valor_respuesta)
            pregunta_actual = pregunta_actual + 1
            if (pregunta_actual <= 3):
                valor_riesgo = valor_riesgo + valor_respuesta
                if (pregunta_actual == 1):
                    message = "¿Que tan seguro te sentis de vos mismo al abordar una tarea de la que no conoces demasiado?"
                elif (pregunta_actual == 2):
                    message = "¿Que tan ajustado estas de tiempo al finalizar tus sprints?"
                elif (pregunta_actual == 3):
                    message = "Del 0 al 5, ¿Cuanto soles pensar que las cosas saldran bien?"
            elif (pregunta_actual <= 6):
                valor_optimismo = valor_optimismo + valor_respuesta
                if (pregunta_actual == 4):
                    message = "¿Que tanto ves el lado bueno de las cosas?"
                elif (pregunta_actual == 5):
                    message = "Del 0 al 5, ¿Usualmente te encuentras de buen humor?"
                elif (pregunta_actual == 6):
                    message = "¿Que tanto confias en las decisiones de los demas por sobre las tuyas?"
            elif (pregunta_actual <= 9):
                valor_adaptabilidad = valor_adaptabilidad + valor_respuesta
                if (pregunta_actual == 7):
                    message = "¿Que tanto seguis la corriente?"
                elif (pregunta_actual == 8):
                    message = "Del 0 al 5, ¿Soles confiar en las decisiones de tus pares?"
                elif (pregunta_actual == 9):
                    message = "En las siguiente preguntas responde con Si o No"
                    dispatcher.utter_message(text=message)
                    message = "¿Tenes conocimientos de devops?"
        else:
            message = "No se reconocio el valor de la respuesta"   
        dispatcher.utter_message(text=message)
        return []

class ActionGuardarConocimiento(Action):
    def name(self) -> Text:
        return "guardar_conocimiento"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global habilidades, lenguajes, pregunta_actual
        nombre_participante = str(tracker.get_slot("participante"))
        pregunta_actual = pregunta_actual + 1
        message = ""
        if (pregunta_actual == 10):
            habilidades.append("devops")
            message = "¿Trabajaste con bases de datos?"
        elif (pregunta_actual == 11):
            habilidades.append("base de datos")
            message = "¿Tenes conocimientos de inteligencia artificial?"
        elif (pregunta_actual == 12):
            habilidades.append("inteligencia artificial")
            message = "¿Realizaste algun trabajo de front-end?"
        elif (pregunta_actual == 13):
            habilidades.append("front-end")
            message = "¿Te sentis comodo programando en Python?"
        elif (pregunta_actual == 14):
            lenguajes.append("python")
            message = "¿Sabes programar en Java?"
        elif (pregunta_actual == 15):
            lenguajes.append("java")
            message = "¿Te gusta programar en C#?"
        elif (pregunta_actual == 16):
            lenguajes.append("c#")
            message = "¿Tenés conocimientos de C?"
        elif (pregunta_actual == 17):
            lenguajes.append("c")
            message = "¿Programas en JavaScript?"
        elif (pregunta_actual == 18):
            lenguajes.append("javascript")
            if darAlta(nombre_participante):
                message = nombre_participante + ", realizaste de forma correcta la prueba de aptitud! Muchas gracias y hasta luego!"
            else: message = "Ocurrio un error al realizar la prueba de aptitud! Vuelva a intentarlo de nuevo."
        dispatcher.utter_message(text=message)
        return []

class ActionNoGuardarConocimiento(Action):
    def name(self) -> Text:
        return "no_guardar_conocimiento"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        global habilidades, lenguajes, pregunta_actual
        pregunta_actual = pregunta_actual + 1
        nombre_participante = str(tracker.get_slot("participante"))
        if (pregunta_actual == 10):
            message = "¿Trabajaste con bases de datos?"
        elif (pregunta_actual == 11):
            message = "¿Tenes conocimientos de inteligencia artificial?"
        elif (pregunta_actual == 12):
            message = "¿Realizaste algun trabajo de front-end?"
        elif (pregunta_actual == 13):
            message = "¿Te sentis comodo programando en Python?"
        elif (pregunta_actual == 14):
            message = "¿Sabes programar en Java?"
        elif (pregunta_actual == 15):
            message = "¿Te gusta programar en C#?"
        elif (pregunta_actual == 16):
            message = "¿Tenes conocimientos de C?"
        elif (pregunta_actual == 17):
            message = "¿Programas en JavaScript?"
        elif (pregunta_actual == 18):
            if darAlta(nombre_participante):
                message = nombre_participante + ", realizaste de forma correcta la prueba de aptitud! Muchas gracias y hasta luego!"
            else: message = "Ocurrio un error al realizar la prueba de aptitud! Vuelva a intentarlo de nuevo."
        dispatcher.utter_message(text=message)
        return []



