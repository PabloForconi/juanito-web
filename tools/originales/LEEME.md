Piezas que el dueño rehízo, adaptó o pasó aparte (no están en E:).
`tools/export_archivo.py` las toma de acá (constante `ORIG`). No editarlas a mano.

`eventos/`: flyers y portadas de eventos, y fotos sueltas.
- `tecnopolis-2015-equipo.jpg`: foto del equipo en Tecnópolis 2015; primera del álbum del evento.

`difusion/`: piezas de difusión de la galería.
- `san-patricio.webp`: reemplaza a `Difusion/Promocional/San Patricio/san_patricio_v1.png`.
- `san-patricio-olla.webp`: pieza nueva de San Patricio (Juanito duende con la olla de oro).
- `dia-del-nino.webp`: reemplaza a `Difusion/Promocional/Dia Niño 2014/Dia_Niño_2014_v1.png`.
- `afiche-twitter.webp`: reemplaza a `Difusion/Promocional/Twitter/Afiche_Twitter_v1.png`.
- `pagalo-como-quieras.webp`: reemplaza a `Difusion/Steam/juanito_descuento.jpg`.
- `puro-games.webp`: reemplaza a `Difusion/Promocional/Puro Games/Pure_Games_v1.png`.
- `the-hum.webp`: reemplaza a `Difusion/Promocional/The Hum/The_Hum_SD.png`.
- `halloween-2014.webp`: reemplaza a `Difusion/Promocional/Halloween 2014/Halloween_2014_HD.png`.
- `navidad-2014.webp`: reemplaza a `Difusion/Promocional/Navidad 2014/Navidad_2014_HD.png`.
- `celestineia.webp`: reemplaza a `Difusion/Promocional/Celestineia/Juanito_Celeste.png`.

`home/`: imágenes de las tarjetas de la home.
- `pirateria.webp`: calavera pirata para la tarjeta de Piratería.
- `juego.webp`: key art cuadrado sin logo para la tarjeta El juego.
- `historia.webp`: gabinete arcade vertical con «INSERT COIN» en pantalla, para la tarjeta Historia.
- `prensa.webp`: diario, micrófono y credencial «PRENSA» para la tarjeta Prensa.
- `prensa-revista.webp`: opción anterior (revista, diario y credencial); no se exporta.
- `videos.webp`: claqueta con play, cámara y auriculares para la tarjeta Videos.
- `videos-titulo.webp`: opción anterior (claqueta con la palabra «VIDEOS»); no se exporta.
- `eventos.webp`: jugador frente al gabinete en una expo, para la tarjeta Eventos.
- `mesa.webp`: caja de Juanito Blockits sobre la mesa, para la tarjeta Juego de mesa.

`prensa/`: logos de medios en su versión original (el sitio los usa en blanco, en `src/assets/prensa/logos/`, 96px de alto).
- `ign.webp`: logo de IGN a color, pasado a blanco para `ign.png`.

`prensa/notas/`: imagen principal de cada nota destacada, bajada de la nota misma (el og:image; en IGN, una captura de la nota porque su portada es de 382px). Se convierten a JPG de hasta 1280px en `src/assets/prensa/notas/`.
- `press-over.png`: logo horizontal de Press Over (blanco), reemplaza al apilado.
- `planned-all-along.png`: logo a color de Planned All Along; en el sitio va en blanco, solo las letras (sin el contorno negro).

## Logo de El Dragón Azul en blanco

`src/assets/juego-de-mesa/logo-dragon-azul-blanco.png` sale de `logo-dragon-azul.png`: lo azul pasa a blanco y lo blanco del logo queda transparente (alfa según el canal mínimo: 60 → opaco, 235 → transparente).

`historia/`: imágenes de hitos de la línea de tiempo (grupo `historia` de `export_archivo.py`, salen a `src/assets/archivo/historia/`).
- `barrio-flash.jpg`: panorámica nocturna del barrio de los primeros prototipos en Flash (2011).
