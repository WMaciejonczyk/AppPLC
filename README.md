# Aplikacja komunikacyjno-algorytmiczna współpracująca ze sterownikiem PLC
## Opis projektu
System gromadzenia oraz analizy danych pochodzących z przemysłowego sterownika PLC. Program umożliwia detekcję anomali w danych procesowych przy użyciu algorytmów klasteryzujących.
### Struktura systemu
`TCPClientGUI.py` - odpowiedzialny jest on za komunikację ze sterownikiem PLC, gromadzenie i przetwarzanie danych, oraz interfejs graficzny użytkownika. <br>
`Analysis.py` - odpowiada za analizę oraz wizualizację otrzymanych wyników.
## Użycie
### Interfejs użytkownika
`python TCPClientGUI.py` lub `python3 TCPClientGUI.py`
### Analiza danych
`python Analysis.py <0/1>` lub `python3 Analysis.py <0/1>` <br>
0 - analiza stanów maszyny; 1 - analiza profilu maszyny
## Autorzy
Piotr Maciejończyk <br>
Wojciech Maciejończyk
