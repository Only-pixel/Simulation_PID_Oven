from flask import Flask, render_template, request, redirect, url_for, session
import json
import plotly
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np

app = Flask(__name__, template_folder='www')
app.config['SECRET_KEY'] = 'hrth43ty5y53eg5efg4e'


@app.route('/', methods=["GET","POST"])
def index():
    if(request.method == "POST"):
        if('op1' in request.form):
            session['mode'] = 1
        elif('op2' in request.form):
            session['mode'] = 2
        elif ('op3' in request.form):
            session['mode'] = 3
        elif ('op4' in request.form):
            session['mode'] = 4
        elif ('op5' in request.form):
            return redirect(url_for('custom'))
        return redirect(url_for('symulacja'))
    else:
        return render_template('index.html',title='Konfiguracja piekarnika')

@app.route('/custom', methods=["GET","POST"])
def custom():
    if (request.method == "POST"):
        session['vent'] = False
        session['temp'] = request.form['temp']
        session['czas'] = request.form['czas']
        if(request.form.get('vent')): session['vent'] = True
        session['otw1'] = request.form['otw1']
        session['mode'] = 5
        return redirect(url_for('symulacja'))
    else:
        return render_template('custom.html', title='Ustawienia niestandardowe')


@app.route('/symulacja')
def symulacja():
    Tp = 0.1
    tryb = session['mode']
    if(tryb==1):
        session['temp'] = 250
        session['czas'] = 10
        session['vent'] = False
        session['otw1'] = 0
        session['nazwa'] = 'Pizza'
        wykres = generujDane(20, 10+25, 250, 1, 0, 10/Tp + 150)
    elif(tryb == 2):
        session['temp'] = 200
        session['czas'] = 90
        session['vent'] = False
        session['otw1'] = 0
        session['nazwa'] = 'Kurczak'
        wykres = generujDane(20, 90 + 25, 200, 3, 20/Tp+120, 90/Tp + 150)
    elif (tryb == 3):
        session['temp'] = 160
        session['czas'] = 32
        session['vent'] = False
        session['otw1'] = 0
        session['nazwa'] = 'Ciasto (brownie)'
        wykres = generujDane(20, 32+25, 160, 3, 5/Tp+120, 32/Tp + 150)
    elif (tryb == 4):
        session['temp'] = 60
        session['czas'] = 120
        session['vent'] = True
        session['otw1'] = 0
        session['nazwa'] = 'Suszenie (morele)'
        wykres = generujDane(20, 120+25, 60, 1, 0, 120/Tp + 150, 0.2)
    else:
        temp = int(session['temp'])
        czas = int(session['czas'])
        vent = session['vent']
        otw1 = int(session['otw1'])
        session['nazwa'] = 'Niestandardowy'
        nazwa = session['nazwa']
        if(vent==False):
            if(otw1>0):
                wykres = generujDane(20, czas+25, temp, 3, (otw1 / Tp)+120, czas/Tp + 150)
            else:
                wykres = generujDane(20, czas+25, temp, 1, 0, czas/Tp + 150)
        else:
            if (otw1 > 0):
                wykres = generujDane(20, czas + 25, temp, 3, (otw1 / Tp)+120, czas / Tp + 150, 0.2)
            else:
                wykres = generujDane(20, czas + 25, temp, 1, 0, czas / Tp + 150, 0.2)
    temp = int(session['temp'])
    czas = int(session['czas'])
    vent = session['vent']
    otw1 = int(session['otw1'])
    nazwa = session['nazwa']
    return render_template('activity.html', title='Symulacja', **locals(), plot=wykres)

#Czesc zasadnicza tworzenia wykresu
def limit(minimum,maximum,value):
    return max(minimum,min(maximum,value))

def generujDane(h0,tsim, hdest, ile_razy_otwarte_drzwi, otwarcie_drzwi, wylacz, beta=0.07):
    A = 3540*0.00012  # pole powierzchni przekroju poprzecznego piekarnika w m^2
    pBeta = beta
    Tp = 0.1  # czas probkowania
    Qdmin = 0.0
    Qdmax = 8.0  #wzmocnienie grzania
    umin = 0.0
    umax = 1.0
    hmin = 20.0
    hmax = 280.0
    kp = 60.0  # kp = [0,100] #wzmocnienie regulatora
    Ti = 0.05 # Ti = [0,10] #czas zdwojenia
    Td = 5  # Td = [0,10] #czas wyprzedzania
    time = int(tsim / Tp)  # czas symulacji
    qd = [0]
    u = [0.0]
    h = [h0]  #jak cieplo jest w piekarniku
    e = [hdest]
    qo = []
    licznik = 0.0 #jak dlugo trzymana jest maksymalna temperatura
    check = 0.0 #ile razy otworze piekarnik
    delay = 2.0/Tp #jak dlugie opoznienie, na cele poprawnego wykresu, [1.5 minuty/ ile probek w tym czasie]
    czas_max_temp = 3/Tp
    temp_delay = 0.0
    licz = 0.0
    for x in range(0, time - 1, 1):
        if x > wylacz:
            beta = 1.0
            Qdmax = Qdmin
            e.append(0)
            u.append(0)
        else:
            e.append(hdest - h[x])
            u.append(limit(umin, umax, kp * ((e[x] - e[x - 1]) + (Tp / Ti) * e[x]) + u[-1]))
        if licznik > 0 and check == 0:
            check += 1
            licznik = 0
            temp_delay = delay
        if temp_delay>0:
            qd.append(Qdmin)
            temp_delay -= 1
            qo.append(beta * 8 * np.sqrt(h[x]))
        else:
            qd.append(limit(Qdmin, Qdmax, u[x] * (Qdmax - Qdmin) / (umax - umin) + Qdmin))
            qo.append(beta * np.sqrt(h[x]))
        if h[x] >= hdest-5: #ile czasu od osiagniecia max temperatury
            licznik += 1
        if check > 0 and check < ile_razy_otwarte_drzwi-1 and x == time - otwarcie_drzwi: #jesli otwieram drzwiczki nie pierwszy ani ostatni raz
            check += 1
            beta = 1.0
            licznik = 0.0
            licz = delay
        if licz > 0: #otwieram dzwiczki, nie pierwsze ani ostatnie otwarcie
            licz -= 1
            if licz == 0:
                beta = pBeta
        h.append(limit(hmin, hmax, Tp/A * (qd[x] - qo[x]) + h[x]))
    fig = make_subplots(rows=3, cols=1, subplot_titles=("Temperatura w piekarniku", "Ciepło", "Uchyb regulacji"))
    fig.add_trace(go.Scatter(x=list(range(0, time, 1)), y=h, mode='lines', name='Temperatura'), row=1, col=1)
    fig.add_trace(go.Scatter(x=list(range(0, time, 1)), y=qd, mode='lines', name='Zwiekszenie ciepla'), row=2, col=1)
    fig.add_trace(go.Scatter(x=list(range(0, time, 1)), y=u, mode='lines', name='Uchyb regulacji'), row=3, col=1)
    fig['layout']['xaxis']['title'] = 'Czas [1 min / 10 checks]'
    fig['layout']['xaxis2']['title'] = 'Czas [1 min / 10 checks]'
    fig['layout']['xaxis3']['title'] = 'Czas [1 min / 10 checks]'
    fig['layout']['yaxis']['title'] = 'Temperatura [C]'
    fig['layout']['yaxis2']['title'] = 'Qd'
    fig['layout']['yaxis3']['title'] = 'u'
    fig_json = fig.to_json()
    return fig_json
