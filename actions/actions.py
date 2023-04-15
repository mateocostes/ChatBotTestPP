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

api_endpoint_set_vector = "http://201.235.167.187:8088/dispatcher/set-vector" # 192.168.0.209:8088
api_endpoint_get_vector = "http://201.235.167.187:8088/dispatcher/get-vector" # 192.168.0.209:8088
diccionarioParticipantes = ""
#Variables utilizadas para guardar los valores
pregunta_actual = 0
valor_riesgo = 0
valor_optimismo = 0
valor_adaptabilidad = 0
habilidades = []
lenguajes = []
direcPreguntas = "actions/preguntas.json"
diccionarioPreguntas = readArchivo(direcPreguntas)

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
    data ["vector"] = crearVector(round(valor_riesgo/cantidadPreguntas("riesgo")), round(valor_optimismo/cantidadPreguntas("optimismo")), round(valor_adaptabilidad/cantidadPreguntas("adaptabilidad")), habilidades, lenguajes) #Casteo el valor a entero y lo divido por la cantidad de preguntas
    r = requests.post(url=api_endpoint_set_vector, json=data)
    #print(data)
    #response = requests.get(url=api_endpoint_get_vector).text
    #print("response: " + response)

def darAlta(nombre_participante) -> bool:
    global pregunta_actual
    if (pregunta_actual == preguntasTotales("habilidades") - 1): #Chequeo si se realizaron de forma correcta todas la preguntas para asi dar de alta
        altaValores(nombre_participante)
        return true
    else:
        return false

def leerPregunta(categoria, posicion, dispatcher):
    message = str(diccionarioPreguntas[categoria][posicion])
    dispatcher.utter_message(text=message)

def cantidadPreguntas(categoria) -> int:
    #print(str(len(diccionarioPreguntas[categoria])))
    return (len(diccionarioPreguntas[categoria]))

def leerTotalPreguntas(categoria, dispatcher):
    for pregunta in diccionarioPreguntas[categoria]:
        message = str(pregunta)
        dispatcher.utter_message(text=message)

def preguntasTotales(categoriaFinal) -> int:
    cantidad = 0
    for keys in diccionarioPreguntas.keys():
        if not (str(keys).__eq__("introduccion")):
            cantidad = cantidad + cantidadPreguntas(keys)
            if str(keys).__eq__(str(categoriaFinal)):
                return cantidad
        
def obtenerHabilidad(posicion) -> Text:
    return(str(diccionarioPreguntas["habilidades"][posicion]))

def accionConocimiento(guarda, dispatcher, tracker):
    global habilidades, lenguajes, pregunta_actual
    nombre_participante = str(tracker.get_slot("participante"))
    message = ""
    print("pregunta_actual: " + str(pregunta_actual))
    print("preguntasTotales: " + str(preguntasTotales("habilidades")))
    if bool(guarda):
        habilidades.append(obtenerHabilidad(pregunta_actual - preguntasTotales("adaptabilidad")))
    if (pregunta_actual < preguntasTotales("habilidades") - 1):
        pregunta_actual = pregunta_actual + 1
        leerPregunta("habilidades", pregunta_actual - preguntasTotales("adaptabilidad"), dispatcher)
    elif (pregunta_actual == preguntasTotales("habilidades") - 1):
        if darAlta(nombre_participante):
            message = nombre_participante + ", realizaste de forma correcta la prueba de aptitud! Muchas gracias y hasta luego!"
        else: message = "Ocurrio un error al realizar la prueba de aptitud! Vuelva a intentarlo de nuevo."
        dispatcher.utter_message(text=message)


class ActionGuardarNombre(Action):

    def name(self) -> Text:
        return "guardar_nombre"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
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
                leerTotalPreguntas("introduccion", dispatcher)
                leerPregunta("riesgo", 0, dispatcher)
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
            if (pregunta_actual < cantidadPreguntas("riesgo")):
                valor_riesgo = valor_riesgo + valor_respuesta
                print(str(valor_riesgo))
                leerPregunta("riesgo", pregunta_actual, dispatcher)
            elif (pregunta_actual < preguntasTotales("optimismo")):
                valor_optimismo = valor_optimismo + valor_respuesta
                leerPregunta("optimismo", pregunta_actual - cantidadPreguntas("riesgo"), dispatcher)
            elif (pregunta_actual < preguntasTotales("adaptabilidad")):
                valor_adaptabilidad = valor_adaptabilidad + valor_respuesta
                leerPregunta("adaptabilidad", pregunta_actual - preguntasTotales("optimismo"), dispatcher)
            else : 
                message = "En las siguiente preguntas responde con Si o No"
                dispatcher.utter_message(text=message)
                leerPregunta("habilidades", 0, dispatcher)
        else:
            message = "No se reconocio el valor de la respuesta"   
            dispatcher.utter_message(text=message)
        return []

class ActionGuardarConocimiento(Action):
    def name(self) -> Text:
        return "guardar_conocimiento"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        accionConocimiento(True, dispatcher, tracker)
        return []

class ActionNoGuardarConocimiento(Action):
    def name(self) -> Text:
        return "no_guardar_conocimiento"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        accionConocimiento(False, dispatcher, tracker)
        return []


