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
valores_categorias = []
habilidades = []
lenguajes = []
direcPreguntas = "actions/preguntas.json"
diccionarioPreguntas = readArchivo(direcPreguntas)
categoriasPreguntas = []
categoria_actual = 0
valor_pregunta = 0
habilidades_lenguajes = 0

def existeParticipante(nombre_participante) -> bool:
    response = requests.get(url=api_endpoint_get_vector).text
    #print("response: " + response)
    diccionarioParticipantes = json.loads(response)
    for participante in diccionarioParticipantes:
        if (participante["nickname"] == nombre_participante):
            return True
    return False

def crearVector():
    global habilidades, lenguajes, categoriasPreguntas
    vector = {}
    for i in range(len(categoriasPreguntas)):
        vector[categoriasPreguntas[i]] = valores_categorias[i]
    vector["habilidades"] = habilidades
    vector["lenguajes"] = lenguajes
    return vector

def altaValores(nombre_partipante) -> bool:
    global habilidades, lenguajes
    data = {}
    data ["agilebotId"] = nombre_partipante
    data ["vector"] = crearVector() #Casteo el valor a entero y lo divido por la cantidad de preguntas
    r = requests.post(url=api_endpoint_set_vector, json=data)
    return r.ok #chequear
    #print(data)
    #response = requests.get(url=api_endpoint_get_vector).text
    #print("response: " + response)

def cantidadPreguntas(categoria) -> int:
    return (len(diccionarioPreguntas["preguntas"][categoria]))

def cantidadRegistros(categoria) -> int:
    return (len(diccionarioPreguntas[categoria]))

def leerIntroduccion(dispatcher):
    for pregunta in diccionarioPreguntas["introduccion"]:
        message = str(pregunta)
        dispatcher.utter_message(text=message)

def obtenerPregunta(categoria, posicion) -> Text:
    return str(diccionarioPreguntas["preguntas"][categoria][posicion])
        
def obtenerRegistro(categoria, posicion) -> Text:
    return(str(diccionarioPreguntas[categoria][posicion]))

def accionConocimiento(guarda, nombre_participante) -> Text:
    global habilidades, lenguajes, pregunta_actual, habilidades_lenguajes
    if habilidades_lenguajes == 0:
        if bool(guarda):
            habilidades.append(obtenerRegistro("habilidades", pregunta_actual))
        pregunta_actual = pregunta_actual + 1
        if (pregunta_actual < cantidadRegistros("habilidades")):
            return generarPreguntaHabilidades(obtenerRegistro("habilidades", pregunta_actual))
        else: 
            habilidades_lenguajes = 1
            pregunta_actual = 0
            return generarPreguntaLenguajes(obtenerRegistro("lenguajes", pregunta_actual))
    else:
        if bool(guarda):
            lenguajes.append(obtenerRegistro("lenguajes", pregunta_actual))
        pregunta_actual = pregunta_actual + 1
        if (pregunta_actual < cantidadRegistros("lenguajes")):
            return generarPreguntaHabilidades(obtenerRegistro("lenguajes", pregunta_actual))
        else: 
            if altaValores(nombre_participante):
                return (nombre_participante + ", realizaste de forma correcta la prueba de aptitud! Muchas gracias y hasta luego!")
            else: return ("Ocurrio un error al realizar la prueba de aptitud! Vuelva a intentarlo de nuevo.")


def generarPreguntaHabilidades(habilidad) -> Text:
    lista_preguntas = []
    pregunta1 = "¿Trabajaste con " + habilidad + "?"
    pregunta2 = "¿Tenes conocimientos de " + habilidad + "?"
    pregunta3 = "¿Realizaste algun trabajo de " + habilidad + "?"
    pregunta4 = "¿Alguna vez hiciste algo con " + habilidad + "?"
    pregunta5 = "¿Tenes habilidades de " + habilidad + "?"
    #AGREGAR MAS EJEMPLOS
    lista_preguntas.append(pregunta1)
    lista_preguntas.append(pregunta2)
    lista_preguntas.append(pregunta3)
    lista_preguntas.append(pregunta4)
    lista_preguntas.append(pregunta5)
    return random.choice(lista_preguntas)

def generarPreguntaLenguajes(lenguaje) -> Text:
    lista_preguntas = []
    pregunta1 = "¿Te sentis comodo programando en " + lenguaje + "?"
    pregunta2 = "¿Sabes programar en " + lenguaje + "?"
    pregunta3 = "¿Te gusta programar en " + lenguaje + "?"
    pregunta4 = "¿Tenés conocimientos de " + lenguaje + "?"
    pregunta5 = "¿Programas en " + lenguaje + "?"
    #AGREGAR MAS EJEMPLOS
    lista_preguntas.append(pregunta1)
    lista_preguntas.append(pregunta2)
    lista_preguntas.append(pregunta3)
    lista_preguntas.append(pregunta4)
    lista_preguntas.append(pregunta5)
    return random.choice(lista_preguntas)

class ActionGuardarNombre(Action):

    def name(self) -> Text:
        return "guardar_nombre"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        nombre_partipante = next (tracker.get_latest_entity_values("participante"),None)
        message = ""
        if (nombre_partipante != None):
            #Reinicio las varibles globales
            global pregunta_actual, habilidades, lenguajes, categoriasPreguntas, categoria_actual
            pregunta_actual = 0
            habilidades = []
            lenguajes = []
            categoriasPreguntas = list(dict(diccionarioPreguntas["preguntas"]).keys())
            print("categorias preguntas: " + str(categoriasPreguntas))
            if(existeParticipante(nombre_partipante)):
                leerIntroduccion(dispatcher)
                message = obtenerPregunta(categoriasPreguntas[categoria_actual], 0) #Se sabe que la categoria tiene preguntas
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
        global habilidades, lenguajes, pregunta_actual, categoria_actual, valor_pregunta #Declaro las variables globales a utilizar
        valor_respuesta = next (tracker.get_latest_entity_values("valor_respuesta"),None)
        message = "Error"        
        if (valor_respuesta != None):
            valor_pregunta = valor_pregunta + int(valor_respuesta)
            pregunta_actual = pregunta_actual + 1
            if pregunta_actual < cantidadPreguntas(categoriasPreguntas[categoria_actual]): #Si seguimos en la misma categoria
                message = obtenerPregunta(categoriasPreguntas[categoria_actual], pregunta_actual)
                dispatcher.utter_message(text=message)
            else:
                valores_categorias.append(round(valor_pregunta/cantidadPreguntas(categoriasPreguntas[categoria_actual])))
                pregunta_actual = 0 #para seguir con las preguntas de la proxima categoria
                categoria_actual = categoria_actual + 1
                if categoria_actual < len(categoriasPreguntas):
                    valor_pregunta = 0
                    message = obtenerPregunta(categoriasPreguntas[categoria_actual], pregunta_actual)
                    dispatcher.utter_message(text=message)
                else: 
                    message = "En las siguientes preguntas respondé con Si o No"
                    dispatcher.utter_message(text=message)
                    message = generarPreguntaHabilidades(obtenerRegistro("habilidades", pregunta_actual))
                    dispatcher.utter_message(text=message)
        else:
            message = "No se reconocio el valor de la respuesta"   
            dispatcher.utter_message(text=message)
        return []

class ActionGuardarConocimiento(Action):
    def name(self) -> Text:
        return "guardar_conocimiento"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        nombre_participante = str(tracker.get_slot("participante"))
        message = accionConocimiento(True, nombre_participante)
        dispatcher.utter_message(text=message)
        return []

class ActionNoGuardarConocimiento(Action):
    def name(self) -> Text:
        return "no_guardar_conocimiento"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        nombre_participante = str(tracker.get_slot("participante"))
        message = accionConocimiento(False, nombre_participante)
        dispatcher.utter_message(text=message)
        return []



