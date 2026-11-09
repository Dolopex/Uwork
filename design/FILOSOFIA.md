# Cauce Claro

Filosofía visual para U-Work.

---

## El movimiento

Cauce Claro es la convicción de que una plataforma de intermediación debe
parecer un cauce: un conducto despejado donde el agua (la información, la
oferta, la contraparte) encuentra su dirección sin obstáculos. No un salón
conmobiliario: no un catálogo de piezas exhibidas. Un cauce es obra de
ingeniería discreta, la clase de estructura que no se admira pero de la que
todo depende. Quien lo cruza rara vez repara en el muro de contención; repara
en que el agua llega.

De ahí sale la regla central: **la forma acompaña a la función y nunca la
supera.** Si un adorno no dice algo, no está. Si un color no codifica un
estado, sobra. Si una sombra no separa dos planos, es ruido.

Esta filosofía no pide una estética; pide una disciplina. El resultado no es
un estilo reconocible, es la sensación de que todo está donde debe estar y
que nada compite por atención.

## Espacio y forma

La forma es sobria y sus ángulos, cuando aparecen, están a un radio
constante que el ojo aprende a leer como una sola familia. Nada es
burbuja, nada es rectángulo afilado: la diferencia entre un borde de seis y
uno de veinticuatro píxeles es la diferencia entre una herramienta y un
juguete, y esta plataforma es una herramienta.

El espacio se organiza en una retícula de cuatro píxeles que se respira en
las costuras. En pantalla angosta, una sola columna, con el contenido
centrado y el aire concentrated en los bordes: el lector no debe encontrar
nada que lo despiste, solo lo que necesita. En pantalla ancha, la misma
columna se convierte en una rejilla medida que reparte el peso sin
inventar jerarquías nuevas. La asimetría aparece donde sirve: en la
relación entre un título y su acción, en el desplazamiento lateral de una
tarjeta sobre un encabezado, en el espacio muerto deliberado que separa
dos familias de información. Nunca como decoración.

## Color y material

Un solo acento, uno solo, y se reserva para lo que el usuario puede hacer:
el botón que actúa, el enlace que lleva, el foco que señala dónde estás.
Todo lo demás es neutro, de una sola familia ñe, del más claro al
más oscuro, sin fluctuar entre familias frías y cálidas dentro del mismo
producto.

El color tiene un único trabajo semántico: **decir qué estado tiene algo.**
Verde es correcto, ámbar es atención, rojo es peligro, azul es
información, gris es quietud. Ese color nunca aparece en un título, nunca
en un borde decorativo, nunca en una sombra. Cuando el acento y el color
de estado coinciden en una misma superficie, manda el estado, porque el
estado es la información, y la acción es un detalle de la interfaz.

Los materiales son lisos y opacos por defecto. La transparencia se reserva
para lo que flota sobre otra cosa (una barra que se solapa a un contenido,
un panel sobre un fondo), y allí nunca es decorativa: es una declaración de
que aquello está por encima. Sufren siempre el mismo aparejo: un borde
interior de un píxel, un brillo interior apenas perceptible en el borde
superior, y una densidad de fondo constante debajo. El cristal sin borde
interior es unaficción; con borde, es un material.

## Escala y ritmo

Una sola escala tipográfica, con pasos que se sienten, no que se notan. Los
titulares aprietan el interletrado y se alinean a la izquierda; el texto de
cuerpo respira a una altura de línea que no cansa; los datos numéricos
llevan cifras tabulares para que las columnas de dinero se alineen solas.
El tamaño de un titular no sube para gritar: sube cuando la composición lo
exige y baja cuando la atención no lo necesita.

El ritmo vertical se construye con un número reducido de pasos. Cada
elemento de la interfaz tiene una altura base, un interlineado y un margen
que lo separa de su vecino. Dos elementos contiguos que no tienen relación
directa se separan más que dos que sí. La diferencia entre "dentro de" y
"al lado de" es una diferencia de espaciado, no de color.

## Composición y balance

Cada pantalla tiene un foco. Uno. Un encabezado que dice dónde estás, una
acción que dice qué puedes hacer, y debajo el contenido en el orden en que
se lee. El equilibrio no es simetría: es que el ojo sepa por dónde entrar
y qué hacer después. Cuando todo tiene el mismo peso visual, no hay
jerarquía, y sin jerarquía el usuario lee todo y no entiende nada.

El material se reparte con justicia: el vidrio y el metal son para lo que
flota y lo que se toca; el papel y la tinta son para lo que se lee. Un
tablero de datos no necesita ser una colección de cajas: necesita líneas,
espacio y alineación. Y cuando un componente tiene que destacar, destaca
por jerarquía, no por contenedor.

## Jerarquía visual

El orden de prioridad es invariable y se respeta sin excepción: **acción,
estado, contenido, metadato.** Lo que el usuario puede hacer se ve primero
y se toca fácil. Lo que está pasando con sus datos se ve segundo, con
color, sin que haya que leerlo. El contenido viene después. Los metadatos,
el autor, la fecha, la etiqueta, van al final y pueden ser discretos,
porque casi nunca son lo que se busca.

Lo que viola este orden es ruido, y el ruido se elimina con una pregunta
por componente: ¿qué información aporta esto? Si la respuesta es "ninguna",
el componente se va.

---

## Formularios

Un formulario largo no se baja: se recorre. La persona que registra su
cuenta para trabajar no está escribiendo un formulario, está contando
quién es, en una secuencia de pasos donde cada uno pide una cosa y
confirma que la tiene.

Por eso los formularios de la casa son asistentes: un paso visible a la
vez, un indicador que dice en cuál se está, y una navegación que deja
volver atrás sin perder lo escrito. El avance nunca depende de que la
persona haya leído hasta el final de una página larga: depende de que
haya llenado lo que ese paso pide.

Cada control dice en qué está. El campo que falla se marca y explica el
motivo sin esperar al envío. La contraseña muestra su fortaleza mientras
se escribe, no después. Las habilidades se anotan como etiquetas y no
como una coma larguísima que nadie puede leer. La imagen que se sube se ve
antes de confirmar. Nada de esto adorna: cada una de estas señales
responde a una pregunta que la persona se está haciendo en ese momento.

El error que viene del servidor no es un castigo: es una indicación de
dónde hay que volver. Por eso el resumen de errores enlaza a cada campo
y el formulario abre el paso que lo contiene. La persona no tiene que
buscar el problema: se le lleva.

Y todo esto vive en un solo lugar. Los tokens y las primitivas están en
`static/css/style.css`, y el comportamiento de los formularios está en
`static/js/wizard.js`. Ninguna plantilla repite el estilo de un campo ni
reimplementa el recorrido de los pasos. Cuando dos pantallas comparten un
patrón, el patrón se escribe una vez.

## Ofício

Nada de esto se improvisa. Una escala de radios que se aplica sin una sola
excepción. Un color de acento que no aparece en dos intensidades
distintas. Una sombra que no lleva el tinte del fondo en el que vive. Un
anillo de foco que se ve igual en cada control de cada pantalla. Un
margen que se calcula, no que se eyeballa. Una línea de texto que nunca
supera la medida cómoda de lectura.

Cada una de estas decisiones se aplica porque se decidió, no porque quedó
así. Se revisan contra una lista antes de declarar terminado cualquier
trabajo, y cuando algo no la cumple, se corrige antes de entregar. El
resultado tiene que parecer el producto de un oficio ejercido durante años:
no la acumulación de decisiones aislada, sino un sistema donde cada pieza
tiene su lugar y su razón.

La diferencia entre una interfaz correcta y una interfaz bella no está en
las piezas: está en que la pieza correcta es la que corresponde, y el
trabajo de terminarla es el de comprobar, una por una, que corresponde.
