# -*- coding: utf-8 -*-
"""
Created on Fri Aug 20 19:24:31 2021

@author: badil
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly_express as px
import plotly.figure_factory as ff
import numpy as np
import scipy.stats



def rendimientos(dfActivos, columna):
    ajustados=dfActivos[[columna]].iloc[1:]
    ajustados['Variaciones']=dfActivos[[columna]].iloc[1:].values/dfActivos[[columna]].iloc[:-1].values -1
    
    return(ajustados)[[columna,'Variaciones']]


class estadisticasRend:
    def __init__(self, simbolo, inicio=datetime(datetime.today().year-1,12,31).strftime('%Y-%m-%d'), fin=(datetime.today().date()+timedelta(days=1)).strftime('%Y-%m-%d')):
        self.simbolo=simbolo
        inicio=datetime.strptime(inicio,'%Y-%m-%d')
        fin=datetime.strptime(fin,'%Y-%m-%d')
        self.activo= yf.download(simbolo, start=inicio, end=fin, progress=True)
        self.rendimientosactivo=rendimientos(self.activo, 'Close')
        self.activo=self.activo.iloc[1:]
        self.mediarend=self.rendimientosactivo['Variaciones'].mean()
        self.varianzarend=self.rendimientosactivo['Variaciones'].var()
        self.volatilidad=np.sqrt(self.varianzarend)
        self.precioInicial=self.activo['Close'][0]
        self.precioFinal=self.activo['Close'][-1]
        self.precioMaximo=self.activo['Close'].max()
        self.precioMinimo=self.activo['Close'].min()
        
        
    def graficaDistribucion(self):
        hist=px.histogram(self.rendimientosactivo, x='Variaciones', nbins=int(np.floor(np.sqrt(self.rendimientosactivo['Variaciones'].size))))
        norm=scipy.stats.norm(self.mediarend, self.volatilidad)
        maximo=1.2*max(abs(self.rendimientosactivo['Variaciones'].max()), abs(self.rendimientosactivo['Variaciones'].min()))
        intervalo=np.linspace(-maximo, maximo,100)
        y=norm.pdf(intervalo)
        fig=px.line(x=intervalo, y=y, color_discrete_sequence =['#FF4500'])
        fig.add_trace(hist.data[0])
        fig.update_layout(title='''Histograma de rendimientos para {} y distribución normal asociada 
                          <br><sup>Rendimiento diario esperado: {:.2%} Rendimiento anual esperado: {:.2%} </sup>
                          <br><sup>Varianza: {:.6%} Desviación estandar: {:.2%} VaR Paramétrico: {:.2%} VaR Histórico: {:.2%} </sup>'''.format(self.simbolo, 
                          self.mediarend, 252*self.mediarend, 
                          self.varianzarend, self.volatilidad,
                          norm.ppf(0.05), self.rendimientosactivo['Variaciones'].quantile(.05)),
            # title='Histograma de Rendimientos para {} y distribución normal asociada </br> Rendimiento medio: {} \ Volatilidad: {}'.format(self.simbolo,self.mediarend,self.volatilidad),
                          xaxis_title='Rendimiento', 
                          yaxis_title='Conteo')
        return(fig)
    def jarqueBeraTest(self, imprime=True):
        JBtest=scipy.stats.jarque_bera(self.rendimientosactivo['Close'])
        if (JBtest[1]<0.05) & imprime:
            print('El p-value es menor a 0.05 no se puede considerar una distribución normal')
        elif imprime:
            print('Se puede considerar una distribución normal')
        
        return(JBtest)
    def graficaPrecios(self, base100=False):
        
        fig=go.Figure(data=go.Scatter(x=self.activo.index, y=self.activo['Close'], name='Precio Cierre'))
        fig.update_layout(title_text='''Precio de {}
                          <br><sup>Mínimo: {:,.2f} Máximo: {:,.2f}</sup>
                          <br><sup>Precio inicial: {:,.2f} Precio Final: {:,.2f} </sup>'''.format(self.simbolo, self.precioMinimo, self.precioMaximo, self.precioInicial, self.precioFinal))
        return(fig)
    
    def graficaRendimientos(self):
        fig=go.Figure(data=go.Bar(x=self.rendimientosactivo.index, y=self.rendimientosactivo['Variaciones'], name='Variaciones'))
        fig.update_layout(title_text='Variaciones en el Precio de '+ self.simbolo)
        fig.update_yaxes(tickformat='%')
        return(fig)  
    def graficaPrecioRendimiento(self):
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True)                                                                                                                                                                                                                                     
        fig.append_trace(self.graficaPrecios()['data'][0], 1,1)
        fig.append_trace(self.graficaRendimientos()['data'][0], 2, 1)
        fig.update_layout(title_text='Precio y variaciones '+ self.simbolo)
        fig.update_yaxes(tickformat='%', row=2, col=1)
        return(fig)
    
class estadisticasPortafolios:
    def __init__(self, listaSimbolos, inicio=datetime(datetime.today().year-1,12,31).strftime('%Y-%m-%d'), fin=(datetime.today().date()+timedelta(days=1)).strftime('%Y-%m-%d')):
        self.listaSimbolos=listaSimbolos
        
        instrumento=estadisticasRend(listaSimbolos[0], inicio, fin)
        
        self.precios=instrumento.activo[['Close']]
        self.precios[listaSimbolos[0]]=self.precios['Close']
        self.precios=self.precios.drop(columns=['Close'])
        
        self.rendimientos=instrumento.rendimientosactivo[['Variaciones']]
        self.rendimientos[listaSimbolos[0]]=self.rendimientos['Variaciones']
        self.rendimientos=self.rendimientos.drop(columns=['Variaciones'])
        
        
        if len(listaSimbolos) > 1:
            for i in [*range(1,len(listaSimbolos))]:
                agregado=estadisticasRend(listaSimbolos[i], inicio, fin)
                
                self.precios=self.precios.join(agregado.activo[['Close']]  , how='inner')
                self.precios[listaSimbolos[i]]=self.precios['Close']
                self.precios=self.precios.drop(columns=['Close'])
                
                self.rendimientos=self.rendimientos.join(agregado.rendimientosactivo[['Variaciones']], how='inner')
                self.rendimientos[listaSimbolos[i]]=self.rendimientos['Variaciones']
                self.rendimientos=self.rendimientos.drop(columns=['Variaciones'])
        self.matCorr=self.rendimientos.corr()
        self.matCov=self.rendimientos.cov()
    def grafMatrices(self, tipo):
        mat=None
        nombre=''
        if tipo=="corr":
            mat=self.matCorr
            nombre='Correlación'
        if tipo=='cov':
            mat=self.matCov
            nombre='Varianzas y Covarianzas'
        
        fig=ff.create_annotated_heatmap(z=mat.to_numpy(),
                                        x=mat.columns.to_list(),
                                        y=mat.columns.to_list(),
                                        colorscale=px.colors.diverging.RdBu)
        fig.update_xaxes(side="bottom")
        fig.update_layout(title_text='Matriz de {}'.format(nombre),
                          xaxis_showgrid=False,
                          yaxis_showgrid=False,
                          xaxis_zeroline=False,
                          yaxis_zeroline=False,
                          yaxis_autorange='reversed',
                          template='plotly_white')
        
        return(fig)
        
        
        
