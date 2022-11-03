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

class ActionGuardarNombre(Action):

    def name(self) -> Text:
        return "guardar_nombre"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        nombre_partipante = next (tracker.get_latest_entity_values("participante"),None)
        message = ""
        print("Nombre Partipante: " + str(nombre_partipante))
        if (nombre_partipante != None):
            print("Existe participante: " + str(bool(existeParticipante(nombre_partipante))))
            if(existeParticipante(nombre_partipante)):
                message = "Hola, vamos a realizar una prueba de aptitud para ver lo que votarias ante ciertas tareas. Ademas, te voy a realizar alguna preguntas para determinar los conocimientos que tenes actualmente."
            else:
                message = "El nombre no corresponde a un AgileBot perteneciente al mundo"
        else:
            message = "No se puede reconocer el nombre del AgileBot"
        dispatcher.utter_message(text=message)
        return [SlotSet("participante",str(nombre_partipante))]

class ActionGuardarValorRespuesta(Action):
    def name(self) -> Text:
        return "guardar_valor_respuesta"
    
    def altaValores(self, nombre_partipante):
        data = {}
        data ["agilebotId"] = nombre_partipante
        data ["vector"] = crearVector(valor_riesgo, valor_optimismo, valor_adaptabilidad, habilidades, lenguajes)
        r = requests.post(url=api_endpoint_set_vector, json=data)
        print(data)

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        valor_respuesta = next (tracker.get_latest_entity_values("valor_respuesta"),None)
        nombre_partipante = str(tracker.get_slot("participante"))
        print("Nombre Partipante: " + str(nombre_partipante))
        if (valor_respuesta != None):
            pregunta_actual =+ 1
            if (pregunta_actual <= 3):
                valor_riesgo =+ valor_respuesta
            elif (pregunta_actual <= 6):
                valor_optimismo =+ valor_respuesta
            elif (pregunta_actual <= 9):
                valor_adaptabilidad =+ valor_respuesta
            else: self.altaValores(nombre_partipante)
        else:
            message = "No se reconocio el valor de la respuesta"   
            dispatcher.utter_message(text=message)
        return []


