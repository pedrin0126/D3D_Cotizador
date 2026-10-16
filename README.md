# Cotizador D3D

App web para cotizar impresiones 3D y generar la cotización en PDF a nombre de D3D.

**Fórmula:** `Precio = (gramos × $/g + horas × $/h) × multiplicador + extras`, redondeado.

## Correr en local
```
pip install -r requirements.txt
streamlit run app.py
```

## Publicar
Desplegar en https://share.streamlit.io apuntando a `app.py`.
