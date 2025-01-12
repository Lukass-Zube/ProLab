# Ievads
Šī projekta problēmsituācija ir basketbola spēles rezultāta prognozēšana. Mūsdienās, lai prognozētu sporta spēles rezultātus, sporta entuziasti pārsvarā balstās uz savu intuīciju. Spēles rezultātu būtiski ietekmē komandas spēlētāju sastāvi, spēlētāju fiziskā forma, un citi faktori, taču, balstoties uz vēsturiskiem datiem par spēļu rezultātiem, iespējams veikt precīzākas prognozes par kādas komandas veiktspēju.

Projekta mērķis ir izveidot tīmekļa lietojumprogrammu, kura, balstoties uz vēsturiskiem basketbola spēļu datiem, nosaka prognozi spēles rezultātam starp divām lietotāja izvēlētajām basketbola komandām. 

# Līdzīgo risinājumu pārskats

| Risinājums | Īss apraksts | Svarīgākās iezīmes | Ierobežojumi
|-----|-----|-----|-----
| NBA rezultātu prognozēšana ar matricām // christopherjenness | Programma izmanto vienskaitļa vērtību dekompozīcijas metodi (SVD), mēģinot sadalīt datu tabulu mazākās daļās, lai novērtētu trūkstošās vērtības (komandas, kuras savā starpā nav spēlējušas) un veiktu prognozes. | Lai veiktu aprēķinus, tiek izmantoti divi rādītāji - uzbrukuma reitings (punktu skaits uz 100 izspēlētām bumbām) un temps (cik bumbu katra komanda iegūst spēlē). | Algoritma datu ieguve notiek ļoti lēni, iegūstot informāciju no ārējiem avotiem. Netiek ņemti vērā komandas aizsardzības rādītāji un individuāli spēlētāju sniegumi (statistika, ievainojumi, utt). |
Mājinieku uzvaras prognozēšana ar gradienta algoritmiem // cmunch1 | Programma izmanto divus gradienta palielināšanas algoritmus - XGBoost un LightGBM - kuri veido lēmumu koku sēriju, izlabojot iepriekšējo koku kļūdas, un, lai precizētu modeļa prognozes, izmanto Scikit-learn varbūtības kalibrēšanu. | Aprēķinos tiek izmantoti vēsturiskie dati gan no komandu, gan individuālās statistikas (iegūtie punkti, metienu precizitāte, piespēļu un atlēkušo bumbu skaits, u.c.). | Programma nespēj aprēķināt konkrētus prognozētus rezultātus. Aplikācijā nav paredzēts izvēlēties konkrētas komandas aprēķiniem, tā aprēķina prognozi uzvarēt visām mājas spēlēm konkrētā dienā.| 
Mājinieku uzvaras prognozēšana ar loģistisko regresiju // JakeKandell | Programma izmanto loģistiskās regresijas metodi, kura veic aprēķinus ar Sigmoīda funkciju. Ar funkciju tiek iegūts skaitlis starp 0 un 1, kurš tiek pārveidots attiecīgā varbūtībā, ka mājinieku komanda uzvarēs. | Izmantotie dati tiek ierobežoti uz 100 uzbrukumiem, lai tos būtu iespējams salīdzināt. Aprēķinos tiek izmantoti astoņi aspekti - mājinieku komanda, uzvaras iespējamība, atlēkušās bumbas, kļūdas, aizsardzības/uzbrukuma novērtējums, +/- un metienu precizitāte. | Programma aprēķina tikai mājinieku iespējamību uzvarēt. Netiek ņemts vērā, kādi spēlētāji piedalās spēlē. Datu iegūšanai paiet 1-3min.
NBA spēļu uzvarētāja prognozēšana ar loģistisko regresiju // michaelstrohl | Programma izmanto loģistiskās regresijas metodi Jupyter Notebook vidē ar spēļu datiem no 2007. līdz 2020.gadam, lai noteiktu 2021.gada spēļu uzvarētāju prognozes.  | Aprēķinos tiek izmantoti vēsturiskie dati no komandu statistikas - uzbrukuma un aizsardzības vērtējumus, rezultatīvās piespēles, atlēkošo bumbu skaits, kļūdu skaits. Dati tiek izgūti no csv faila, kas paātrina programmas darbību. |  Spēles, kur abu komandu kopējais izspēlēto spēļu skaits nesasniedz 20, netiek ņemtas vērā. Kā arī netiek ņemti vērā katra spēlētāja individuālie sniegumi.
NBA uzvaru reitinga prognoze // Enayar478 | Programma izmanto lineāro regresiju, lai prognozētu atsevišķu spēlētāju uzvaras reitingu. Pamatā ir detalizēta spēlētāju statistika, uzsverot katra spēlētāja ieguldījumu komandas uzvarās. | Aprēķinos tiek izmantoti dati par konkrētā basketbolista spēlētajām minūtēm, izspēlētajiem uzbrukumiem,  attiecību starp nospēlētajām minūtēm aizsardzībā/uzbrukumā, ietekmi uz komandas izspēlētajiem uzbrukumiem 48 minūšu laikā. | Modelis ir paredzēts spēlētāju reitingu prognozēšanai, nevis spēles iznākumu prognozēšanai.

# Konceptu modelis


![image](https://github.com/user-attachments/assets/ee632a4d-7e50-4185-b4f5-1a789edc5f96)

Lietotājs: sistēmas galvenais lietotājs <br>
Basketbola komandas: lietotāja ievadītie basketbola komandu nosaukumi <br>
Publiska basketbola spēļu datubāze: datubāze, kur tiek izgūta nepieciešamā statistika <br>
Basketbola spēļu statistika: dati, kas tiek izmantoti prognozes veikšanai <br>
Prognozēšanas algoritms: atbilstoši iegūtajiem datiem izvēlēts algoritms <br>
Prognozēšanas rezultāti: algoritma veiktā prognoze <br>
Prognožu analīze: vizuāls prognožu attēlojums


# Tehnoloģiju steks

| Servera puse | Klienta puse |
|--------------|--------------|
| Tīmekļa serveris: Apache | Vide: tīmekļa pārlūks |
| Programmēšanas valoda: Python | Programmēšanas valoda: HTML |
| Satvars: Flask | Programmēšanas valoda: CSS |
| Datu bāze: MongoDB | Programmēšanas valoda: JavaScript |
| OS: Ubuntu |
| Izvietošana: Azure App Service |

# Programmatūras apraksts

Šī programmatūra ir tīmekļa lietojumprogramma, kas izvietota Azure App Service platformā. Sistēma ir integrēta ar GitHub repozitoriju, no kura tā automātiski ielādē kodu no galvenā (main) zara, nodrošinot jaunākās versijas izvietošanu un darbību. Azure App Service nodrošina stabilu un uzticamu programmas hostēšanu.

Programmatūra izmanto MongoDB datubāzi, kas tiek hostēta Atlas platformā. Datubāze kalpo ne tikai vēsturisko basketbola spēļu rezultātu uzglabāšanai, bet arī lietotāju veidoto prognožu glabāšanai. Šī funkcionalitāte ļauj saglabāt personalizētus lietotāju datus un analizēt prognožu precizitāti ilgtermiņā.

Sistēma nodrošina pilnīgi automatizētu darbplūsmu, sākot no koda izvietošanas līdz datubāzes piekļuvei un datu apstrādei, tādējādi piedāvājot efektīvu un viegli uzturamu risinājumu, kas ļauj lietotājiem saņemt precīzas prognozes un iegūt ieskatu savās vēsturiskajās prognozēs.

# Lietotāju stāsti

| Nr. | Lietotāja stāsti | Izpildīts (Jā/Nē)| Komentārs
|--|-------|---|-------
|1.|Lietotājs vēlas saņemt precīzu rezultāta prognozi par basketbola spēlēm, jo tas palīdzēs pieņemt labākus lēmumus likmju likšanā un palielināt ienākumus.|Jā|Algoritms ir izveidots, lai nodrošinātu precīzu prognožu aprēķinu, izmantojot vēsturiskos datus|
2.|Lietotājs vēlas, lai dati tiktu attēloti grafiski, jo tas padarīs informāciju vieglāk uztveramu un analizējamu.|Jā|Ir pievienoti grafiki, kas atvieglo datu analīzi un lietotāja pieredzi.|
3.|Lietotājs vēlas autentificēties sistēmā, jo tas nodrošinās darījumu un prognožu vēstures saglabāšanu.|Jā|Sistēmā ir ieviesta droša lietotāja autentifikācija|
4.|Lietotājs vēlas intuitīvi saprotamu mājas lapu, jo tā nodrošinās vieglu piekļuvi informācijai un uzlabos lietotāja pieredzi.|Jā|Mājas lapa ir izstrādāta ar vienkāršu un intuitīvu navigāciju, lai lietotāji varētu viegli atrast nepieciešamo informāciju.|

# Risinājuma novērtējums

**Problēmsituācija:**  Basketbola spēles rezultāta prognozēšana.

**Eksperimenta mērķis:** Noteikt prognozi spēles rezultātam starp divām lietotāja izvēlētajām komandām.

**Ieejas parametri:** *lietotāja ievadīti* - 1. komandas nosaukums, 2. komandas nosaukums, vēsturisko spēļu skaits *(5, 10, 15, 20, 25)*

**Novērtēšanas mēri:** 1. komandas rezultāta novirze, 2. komandas rezultāta novirze

**Eksperimenti:**

<img width="708" alt="Screenshot 2025-01-12 at 23 02 39" src="https://github.com/user-attachments/assets/cc20dacf-1382-432e-9c98-4b3cb6baddc3" />

### Statistika:

Vidēji prognozētā rezultāta novirze no reālā rezultāta ir +/- 6,04 punkti.  
- Ja tiek izvēlētas 5 komandas, tad novirze ir vidēji +/- 5,9 punkti  
- Ja tiek izvēlētas 10 komandas, tad novirze ir vidēji +/- 5,7 punkti  
- Ja tiek izvēlētas 15 komandas, tad novirze ir vidēji +/- 6,5 punkti  
- Ja tiek izvēlētas 20 komandas, tad novirze ir vidēji +/- 6 punkti  
- Ja tiek izvēlētas 25 komandas, tad novirze ir vidēji +/- 6,2 punkti  
