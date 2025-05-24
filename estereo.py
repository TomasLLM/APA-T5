'''
Práctica 5: Sonido estéreo y ficheros WAVE

Autor: Tomàs Lloret Martínez
Fecha: 16/05/25

Funciones de tratamiento de señales estéreo WAVE de 16 bits.
'''

import struct as st

def leer_encabezado_wave(f):
    '''
    Lee y valida la cabecera de un fichero WAVE.
    '''
    cabecera = f.read(44)
    if len(cabecera) != 44 or cabecera[:4] != b'RIFF' or cabecera[8:12] != b'WAVE':
        raise ValueError("Formato WAVE no válido")
    return cabecera

def escribir_encabezado_wave(f, cabecera, nframes, ncanales=1, samplewidth=2):
    '''
    Modifica y escribe la cabecera de un fichero WAVE con los nuevos parámetros:
    número de frames, número de canales y ancho de muestra.
    '''
    subchunk2size = nframes * ncanales * samplewidth
    chunk_size = 36 + subchunk2size
    cabecera = bytearray(cabecera)
    st.pack_into('<I', cabecera, 4, chunk_size)
    st.pack_into('<H', cabecera, 22, ncanales)
    st.pack_into('<I', cabecera, 28, 44100 * ncanales * samplewidth)
    st.pack_into('<H', cabecera, 32, ncanales * samplewidth)
    st.pack_into('<I', cabecera, 40, subchunk2size)
    f.write(cabecera)

def estereo2mono(ficEste, ficMono, canal=2):
    '''
    Convierte un fichero WAVE estéreo a mono.
    '''
    with open(ficEste, 'rb') as fe:
        cab = leer_encabezado_wave(fe)
        datos = fe.read()
    muestras = st.unpack('<' + 'h' * (len(datos) // 2), datos)
    izq = muestras[::2]
    der = muestras[1::2]
    if canal == 0:
        mono = izq
    elif canal == 1:
        mono = der
    elif canal == 2:
        mono = [(l + r) // 2 for l, r in zip(izq, der)]
    elif canal == 3:
        mono = [(l - r) // 2 for l, r in zip(izq, der)]
    else:
        raise ValueError("Canal no válido")
    with open(ficMono, 'wb') as fm:
        escribir_encabezado_wave(fm, cab, len(mono), ncanales=1)
        fm.write(st.pack('<' + 'h' * len(mono), *mono))

def mono2estereo(ficIzq, ficDer, ficEste):
    '''
    Reconstruye una señal estéreo a partir de dos ficheros mono (izquierdo y derecho).
    '''
    with open(ficIzq, 'rb') as fi:
        cab_izq = leer_encabezado_wave(fi)
        datos_izq = fi.read()
    with open(ficDer, 'rb') as fd:
        cab_der = leer_encabezado_wave(fd)
        datos_der = fd.read()
    datos_izq = st.unpack('<' + 'h' * (len(datos_izq) // 2), datos_izq)
    datos_der = st.unpack('<' + 'h' * (len(datos_der) // 2), datos_der)
    if len(datos_izq) != len(datos_der):
        raise ValueError("Los ficheros mono no tienen la misma longitud")
    intercalado = [val for par in zip(datos_izq, datos_der) for val in par]
    with open(ficEste, 'wb') as fe:
        escribir_encabezado_wave(fe, cab_izq, len(datos_izq), ncanales=2)
        fe.write(st.pack('<' + 'h' * len(intercalado), *intercalado))

def codEstereo(ficEste, ficCod):
    '''
    Codifica una señal estéreo en un fichero monofónico de 32 bits.
    Guarda la semisuma en los 16 bits altos y la semidiferencia en los bajos.
    '''
    with open(ficEste, 'rb') as fe:
        cab = leer_encabezado_wave(fe)
        datos = fe.read()
    muestras = st.unpack('<' + 'h' * (len(datos) // 2), datos)
    izq = muestras[::2]
    der = muestras[1::2]
    codificada = []
    for l, r in zip(izq, der):
        s = (l + r) >> 1
        d = (l - r) >> 1
        codificada.append((s << 16) | (d & 0xFFFF))
    with open(ficCod, 'wb') as fc:
        escribir_encabezado_wave(fc, cab, len(codificada), ncanales=1, samplewidth=4)
        fc.write(st.pack('<' + 'i' * len(codificada), *codificada))

def decEstereo(ficCod, ficEste):
    '''
    Decodifica una señal monofónica de 32 bits en un fichero WAVE estéreo.
    Recupera los canales izquierdo y derecho a partir de semisuma y semidiferencia.
    '''
    with open(ficCod, 'rb') as fc:
        cab = leer_encabezado_wave(fc)
        datos = fc.read()
    muestras = st.unpack('<' + 'i' * (len(datos) // 4), datos)
    izq = [((x >> 16) + (x & 0xFFFF if x & 0x8000 == 0 else x | ~0xFFFF)) // 2 for x in muestras]
    der = [((x >> 16) - (x & 0xFFFF if x & 0x8000 == 0 else x | ~0xFFFF)) // 2 for x in muestras]
    intercalado = [val for par in zip(izq, der) for val in par]
    with open(ficEste, 'wb') as fe:
        escribir_encabezado_wave(fe, cab, len(izq), ncanales=2)
        fe.write(st.pack('<' + 'h' * len(intercalado), *intercalado))