# Ievads
Šī projekta problēmsituācija ir basketbola spēles rezultāta prognozēšana. 

Mērķis ir izveidot tīmekļa lietojumprogrammu, kura, balstoties uz vēsturiskiem basketbola spēļu datiem, nosaka prognozi spēles rezultātam starp divām lietotāja izvēlētajām komandām.

# Līdzīgo risinājumu pārskats

| Risinājums | Īss apraksts | Svarīgākās iezīmes | Ierobežojumi
|-----|-----|-----|-----
| NBA rezultātu prognozēšana ar matricām // christopherjenness | Programma izmanto vienskaitļa vērtību dekompozīcijas metodi (SVD), mēģinot sadalīt datu tabulu mazākās daļās, lai novērtētu trūkstošās vērtības (komandas, kuras savā starpā nav spēlējušas) un veiktu prognozes. | Lai veiktu aprēķinus, tiek izmantoti divi rādītāji - uzbrukuma reitings (punktu skaits uz 100 izspēlētām bumbām) un temps (cik bumbu katra komanda iegūst spēlē). | Algoritma datu ieguve notiek ļoti lēni, iegūstot informāciju no ārējiem avotiem. Netiek ņemti vērā komandas aizsardzības rādītāji un individuāli spēlētāju sniegumi (statistika, ievainojumi, utt). |
Mājinieku uzvaras prognozēšana ar gradienta algoritmiem // cmunch1 | Programma izmanto divus gradienta palielināšanas algoritmus - XGBoost un LightGBM - kuri veido lēmumu koku sēriju, izlabojot iepriekšējo koku kļūdas, un, lai precizētu modeļa prognozes, izmanto Scikit-learn varbūtības kalibrēšanu. | Aprēķinos tiek izmantoti vēsturiskie dati gan no komandu, gan individuālās statistikas (iegūtie punkti, metienu precizitāte, piespēļu un atlēkušo bumbu skaits, u.c.). | Programma nespēj aprēķināt konkrētus prognozētus rezultātus. Aplikācijā nav paredzēts izvēlēties konkrētas komandas aprēķiniem, tā aprēķina prognozi uzvarēt visām mājas spēlēm konkrētā dienā.| 
Mājinieku uzvaras prognozēšana ar loģistisko regresiju // JakeKandell | Programma izmanto loģistiskās regresijas metodi, kura veic aprēķinus ar Sigmoīda funkciju. Ar funkciju tiek iegūts skaitlis starp 0 un 1, kurš tiek pārveidots attiecīgā varbūtībā, ka mājinieku komanda uzvarēs. | Izmantotie dati tiek ierobežoti uz 100 uzbrukumiem, lai tos būtu iespējams salīdzināt. Aprēķinos tiek izmantoti astoņi aspekti - mājinieku komanda, uzvaras iespējamība, atlēkušās bumbas, kļūdas, aizsardzības/uzbrukuma novērtējums, +/- un metienu precizitāte. | Programma aprēķina tikai mājinieku iespējamību uzvarēt. Netiek ņemts vērā, kādi spēlētāji piedalās spēlē. Datu iegūšanai paiet 1-3min.
NBA spēļu uzvarētāja prognozēšana ar loģistisko regresiju // michaelstrohl | Programma izmanto loģistiskās regresijas metodi Jupyter Notebook vidē ar spēļu datiem no 2007. līdz 2020.gadam, lai noteiktu 2021.gada spēļu uzvarētāju prognozes.  | Aprēķinos tiek izmantoti vēsturiskie dati no komandu statistikas - uzbrukuma un aizsardzības vērtējumus, rezultatīvās piespēles, atlēkošo bumbu skaits, kļūdu skaits. Dati tiek izgūti no csv faila, kas paātrina programmas darbību. |  Spēles, kur abu komandu kopējais izspēlēto spēļu skaits nesasniedz 20, netiek ņemtas vērā. Kā arī netiek ņemti vērā katra spēlētāja individuālie sniegumi.
NBA uzvaru reitinga prognoze // Enayar478 | Programma izmanto lineāro regresiju, lai prognozētu atsevišķu spēlētāju uzvaras reitingu. Pamatā ir detalizēta spēlētāju statistika, uzsverot katra spēlētāja ieguldījumu komandas uzvarās. | Aprēķinos tiek izmantoti dati par konkrētā basketbolista spēlētajām minūtēm, izspēlētajiem uzbrukumiem,  attiecību starp nospēlētajām minūtēm aizsardzībā/uzbrukumā, ietekmi uz komandas izspēlētajiem uzbrukumiem 48 minūšu laikā. | Modelis ir paredzēts spēlētāju reitingu prognozēšanai, nevis spēles iznākumu prognozēšanai.

# Konceptu modelis


![image](https://github.com/user-attachments/assets/07d779ea-76dc-407f-b32a-f3283758e19c)

Lietotājs: Sistēmas galvenais lietotājs.
Lietotāja saskarne: Nodrošina saskarsmi starp lietotāju un sistēmu.
Datu avoti: Kur tiek iegūti dati par spēlēm, komandām un spēlētājiem.
Datu apstrāde: Dati tiek sagatavoti modeļa apmācībai.
Modeļa apmācība: Algoritms tiek apmācīts, lai atpazītu modeļus datos.
Prognozēšanas algoritms: Algoritms izdara prognozes.
Prognozes rezultāti: Parāda prognozes lietotājam.
Atsauksme: Lietotājs var sniegt atsauksmi, lai uzlabotu sistēmu.


# Tehnoloģiju stack

Satvars: Flask
Programmēšanas valoda: Python
Datu bāze: MongoDB
Tīmekļa serveris: Apatche
OS: Ubuntu
Hosting: Azure App Service