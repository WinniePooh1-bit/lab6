# Лабораторийн ажил №6 — Тест тохиолдол боловсруулах: Category-Partition ба PICT

**Оюутны нэр:** М.Наранбат  
**Оюутны код:** B242270801  
**Хичээл:** F.CSA313 — Программ хангамжийн чанарын баталгаа ба тест (2026)

## Зорилго

Энэ лабораторид банкны шилжүүлгийн POST /transfer функцэд Category-Partition аргаар тестийн сонголт, төлөөлөх утга, [ERROR], [SINGLE], [IF/property] хязгаарлалтууд болон спецификаци гаргав. Дараа нь Microsoft PICT-ээр browser загварын 2-way, 3-way covering array болон шилжүүлгийн гурван моделийг үүсгэж, гараар зохиосон тест дизайнтай харьцуулсан. Лабораторийн үндсэн бүтээгдэхүүн нь тест дизайны хүснэгтүүд, PICT model файлууд болон үр дүнгийн текст нотолгоо юм; шилжүүлгийн API код бичих даалгавар биш.

## Хэсэг A — Category-Partition: Банкны шилжүүлэг

Тестлэх функц:

    POST /transfer
    { "from": ID, "to": ID, "amount": NUM, "currency": CODE }

Шалгах дүрэм:
- from данс байх ёстой, царцаагдаагүй байх ёстой.
- to данс байх ёстой, from данстай ижил биш байх ёстой.
- amount > 0; хөрвүүлсний дараах дүн from дансны үлдэгдэл болон өдрийн үлдсэн лимитээс хэтрэхгүй.
- currency нь дансны валютаас өөр бол ханшийн хөрвүүлэлт хийнэ.
- Амжилттай: HTTP 201, {"result":"OK"}. Оролтын алдаа: HTTP 200, {"result":"ERROR_..."}.

### Давуу эрэмбэ (олон алдаа нэг хүсэлтэд зэрэг байвал)

Тодорхойлолтод алдааны давуу эрэмбийг тогтоогоогүй тул энэ тайланд дараах дарааллыг өөрийн тестийн oracle болгон сонгов:

**from шалгалт → to шалгалт → amount шалгалт.**

from бүлэг дотроо ERROR_NO_FROM нь ERROR_FROZEN-оос өмнө; to бүлэгт ERROR_NO_TO нь ERROR_SAME_ACCOUNT-оос өмнө; amount бүлэгт ERROR_BAD_AMOUNT → ERROR_INSUFFICIENT → ERROR_LIMIT гэсэн дараалалтай. Ингэснээр давхар алдааны мөр бүрд ганц тодорхой хүлээгдэх үр дүн байна.

### A1. Сонголт ба төлөөлөх утгууд

| Параметр | Сонголт / эквивалент анги | Төлөөлөх утга | Tag ба үндэслэл |
|---|---|---|---|
| from | Valid | ACC001, active | [IF/property] Бусад параметрийн алдааг бие даан шалгах үндсэн хүчинтэй эх данс. |
| from | Frozen | ACC_FROZEN | [ERROR][SINGLE] Данc байна, гэхдээ царцаалттай; ганц эх дансны алдаа болгон шалгана. |
| from | Missing | ACC404 | [ERROR][SINGLE] Системд байхгүй эх дансыг тусад нь шалгана. |
| to | Valid | ACC002 | [IF/property] Хүчинтэй хүлээн авагч; эх данс болон дүнгийн тестэд суурь утга. |
| to | Missing | ACC404 | [ERROR][SINGLE][IF from=Valid] Байхгүй хүлээн авагчийн алдааг эх данс хүчинтэй үед тусгаарлана. |
| to | SameAsFrom | ACC001 | [ERROR][SINGLE][IF from=Valid] Хүлээн авагч нь эх данстай ижил; эх данс байгаа үед л утгатай. |
| amount | Normal | Эерэг, хөрвүүлсний дараа үлдэгдэл ба лимитэд багтах | [IF/property] Алдааны бус үндсэн дүн; дансны алдааг шалгахдаа ашиглана. |
| amount | Zero | 0 эсвэл сөрөг дүн | [ERROR][SINGLE][IF from=Valid AND to=Valid] Бусад нөхцөл хүчинтэй үед дүнгийн алдааг дангаар шалгана. |
| amount | OverBalance | Хөрвүүлсний дараах дүн > үлдэгдэл, гэхдээ өдрийн үлдсэн лимитэд багтана | [ERROR][SINGLE][IF from=Valid AND to=Valid] Зөвхөн үлдэгдлийн алдааг тусгаарлана. |
| amount | OverLimit | Хөрвүүлсний дараах дүн > өдрийн үлдсэн лимит, гэхдээ үлдэгдэлд багтана | [ERROR][SINGLE][IF from=Valid AND to=Valid] Зөвхөн өдрийн лимитийн алдааг тусгаарлана. |
| currency | Same | Дансны валюттай ижил, жишээ нь MNT | [IF/property] Хөрвүүлэлтгүй үндсэн төлөв; алдааны тестүүдэд ашиглана. |
| currency | Different | Дансны валютаас өөр, жишээ нь USD | [SINGLE][IF from=Valid AND to=Valid AND amount=Normal] Ханшийн хөрвүүлэлтийн эерэг замыг тусдаа шалгана. |

### Далд орчны сонголтууд

from, to, amount, currency-гээс гадна тестийн setup-д бэлтгэх шаардлагатай орчны төлөвүүд байна.

| Далд төлөв | Ангилал / setup | Ямар сонголтод нөлөөлөх вэ |
|---|---|---|
| Эх дансны төлөв | Байгаа / байхгүй; active / frozen | from-ийн Valid, Missing, Frozen сонголт |
| Эх дансны үлдэгдэл | Шилжүүлгийн хөрвүүлсэн дүнгээс бага / их | OverBalance ба Normal |
| Өдрийн үлдсэн лимит | Шилжүүлгийн хөрвүүлсэн дүнгээс бага / их | OverLimit ба Normal |
| Валютын ханш | Same currency / өөр валютын хүчинтэй ханш бэлэн | Currency Same, Different |
| Хөрвүүлэлтийн дараах дүн | Үлдэгдэл ба лимиттэй харьцуулах дүн | amount-ийн OverBalance, OverLimit ангилал |

OverBalance тестэд үлдсэн өдрийн лимитийг дүнгээс их, харин үлдэгдлийг бага байлгана. OverLimit тестэд эсрэгээр нь үлдэгдлийг дүнгээс их, өдрийн лимитийг бага байлгана. Ийм setup нь ERROR_INSUFFICIENT болон ERROR_LIMIT-ийг хооронд нь андуурахгүй шалгах боломж өгнө.

### A2. Хязгаарлалт ба N → M тооцоо

Параметрийн сонголтын үржвэрээр бүрэн олонлог:

**N = 3 (from) × 3 (to) × 4 (amount) × 2 (currency) = 72 боломж.**

[ERROR] сонголтуудыг [SINGLE] байдлаар тусгаарлаж, [IF/property] хязгаарлалтаар тухайн алдааг бусад хүчинтэй үндсэн утгатай хослуулна. Хязгаарлалттай transfer.model-д дараах дүрмүүдийг хэрэглэв:

1. from нь Frozen эсвэл Missing бол to=Valid, amount=Normal, currency=Same.
2. to нь Missing эсвэл SameAsFrom бол from=Valid, amount=Normal, currency=Same.
3. amount нь Zero, OverBalance эсвэл OverLimit бол from=Valid, to=Valid, currency=Same.
4. Currency=Different зөвхөн бүх үндсэн нөхцөл хүчинтэй, amount=Normal үед орно.

Үүний үр дүнд 7 ганц алдааны тохиолдол, 1 happy path (Same currency), 1 валют хөрвүүлэлтийн happy path (Different currency) үлдэнэ. Иймээс хязгаарлалтын дараах семантикийн олонлог **M = 9**, өөрөөр хэлбэл **72 → 9**.

### A3. Гар аргаар боловсруулсан спецификацийн хүснэгт

| № | from | to | amount | currency | Хүлээгдэх үр дүн |
|---:|---|---|---|---|---|
| 1 | Valid | Valid | Normal | Same | HTTP 201 — OK (happy path) |
| 2 | Valid | Valid | Normal | Different | HTTP 201 — OK (ханш хөрвүүлэлт) |
| 3 | Missing | Valid | Normal | Same | HTTP 200 — ERROR_NO_FROM |
| 4 | Frozen | Valid | Normal | Same | HTTP 200 — ERROR_FROZEN |
| 5 | Valid | Missing | Normal | Same | HTTP 200 — ERROR_NO_TO |
| 6 | Valid | SameAsFrom | Normal | Same | HTTP 200 — ERROR_SAME_ACCOUNT |
| 7 | Valid | Valid | Zero | Same | HTTP 200 — ERROR_BAD_AMOUNT |
| 8 | Valid | Valid | OverBalance | Same | HTTP 200 — ERROR_INSUFFICIENT |
| 9 | Valid | Valid | OverLimit | Same | HTTP 200 — ERROR_LIMIT |
| 10 | Missing | Missing | Zero | Same | HTTP 200 — ERROR_NO_FROM (from алдаа to/amount-аас түрүүлнэ) |
| 11 | Frozen | Missing | Zero | Same | HTTP 200 — ERROR_FROZEN (from алдаа to/amount-аас түрүүлнэ) |

10, 11-р мөрүүд нь зөвхөн ганц алдааг шалгах бус, сонгосон давуу эрэмбэ олон алдаа зэрэгцсэн үед тогтвортой oracle өгч байгааг шалгана. Эдгээр давхар алдааны кейсийг PICT-ийн single-negative model-д зориуд оруулаагүй; manual спецификацид тусад нь барьсан.

## Хэсэг B — Microsoft PICT pairwise covering array

PICT source-ийг лабораторийн репозиториос гадуур түр хавтаст clone хийж, CMake-ээр Release хувилбарыг build хийнэ. Build-ийн нотолгоонд эх кодын commit болон CLI usage орно. PICT source болон build хавтас репозиторт орохгүй. Үр дүн бүрийг results/ дотор текст хэлбэрээр хадгална. Санамсаргүй /r seed ашиглахгүй тул ижил PICT source ба моделийг дахин ажиллуулахад давтагдах үр дүн гарна.

### B1. Браузерын загвар

browser.model нь Content, Cookies (тус бүр 3 утга), Popups, Addons, Attacks, Forgeries (тус бүр 2 утга) гэсэн 6 параметртэй. Бүрэн олонлог нь **3 × 3 × 2 × 2 × 2 × 2 = 144** хослол.

<!-- PICT-ANALYSIS-START -->

- Browser-ийн бүрэн оролтын олонлог: **144**; 3-way PICT мөр: **20**.
- 2-way browser мөр: **10**. Лекцийн гараар хийсэн 9 мөртэй харьцуулахад олон мөр гарсан. PICT greedy алгоритм нь тухайн алхамд хамгийн олон шинэ хосыг хамруулах сонголт хийдэг ч глобал хамгийн цөөн мөрийн оптимумыг баталгаажуулдаггүй.
- Category-Partition-ийн зөвшөөрөгдсөн олонлог 72-оос 9 болсон (**72 → 9**). PICT constrained model 8 мөрөөр эдгээр хувилбарын бүх боломжит pairwise хосыг бүрхсэн; бүх tuple-ийг тус тусад нь хэвлэх шаардлагагүй.
- transfer-neg output дотор 14 мөр дор хаяж нэг сөрөг утгатай бөгөөд долоон сөрөг сонголт бүгд орсон.

<!-- PICT-ANALYSIS-END -->

PICT greedy алгоритм нь өмнө хамрагдаагүй хосуудыг аль болох олноор нь хамруулах дараагийн мөрийг сонгодог. Гэвч энэ арга нь бүх боломжит багцаас глобал хамгийн цөөн мөрийг олох математик баталгаа өгдөггүй. Тиймээс PICT-ийн 2-way мөрийн тоо лекцийн гараар зохиосон 9 мөрөөс их байж болно. 3-way туршилт нь 144 бүрэн мөр үүсгэхгүйгээр параметрүүдийн бүх гурвалсан утгын хослолыг хамруулах зорилготой.

### B2. Шилжүүлгийн PICT загварууд

| Файл | Зорилго |
|---|---|
| transfer-nc.model | IF хязгаарлалтгүй суурь загвар; нэг мөрөнд хэд хэдэн бизнесийн алдаа зэрэг орж болно. |
| transfer.model | A2-ын IF/property хязгаарлалтуудтай; алдааны ангиудыг тусгаарлаж, зөвшөөрөгдөөгүй хослолыг арилгана. |
| transfer-neg.model | Invalid сонголтуудыг ~ тэмдэгтээр тэмдэглэнэ; PICT нэг мөрөнд нэгээс олон сөрөг утга оруулахгүй. |

<!-- PICT-COUNTS-START -->

| PICT модель / гаралт | Мөрийн тоо | Тайлбар |
|---|---:|---|
| browser 2-way | 10 | Pairwise бүх хосын утгыг хамруулсан |
| browser 3-way | 20 | Бүрэн Cartesian оролтын олонлог 144; 3-way tuple бүгд хамрагдсан |
| transfer-nc (хязгаарлалтгүй) | 13 | 2-way; олон алдаатай хослол үүсч болно |
| transfer (A2 хязгаарлалттай) | 8 | 9 зөвшөөрөгдсөн CP хувилбарын pairwise бүрхүүл |
| transfer-neg (~ сөрөг утгатай) | 16 | Нэг мөрөнд хамгийн ихдээ нэг сөрөг утга |

<!-- PICT-COUNTS-END -->

[ERROR] сонголтыг энгийн утга шиг бичсэн transfer-nc.model-д олон буруу төлөв нэг мөрөнд хосолж, error masking үүсч болно. transfer.model-ийн IF/property хязгаарлалтууд алдааны тестийг нэг нэгээр нь авч, currency conversion-ийг хүчинтэй happy path-д тусгаарласан. transfer-neg.model-д ~ тэмдэглэгээ ашигласнаар PICT өөрөө нэг мөрөнд хамгийн ихдээ нэг negative утга оруулна. Иймээс зөвхөн алдааг давхардуулахгүй байх зорилгоор A2-ын IF хязгаарлалтыг дахин бичих шаардлагагүй; харин домэйны бодит хамаарал, setup шаардлага (жишээ нь үлдэгдэл ба лимитийн нөхцөл) тайлбарлагдсан хэвээр байх ёстой.

### PICT гаралтаас бодит тест кейс болгох

Доорх гурван мөрийг transfer-neg.txt бодит гаралтаас сонгон, дансны setup + хүсэлтийн body + oracle болгон буулгана. ~ тэмдэг нь моделийн сөрөг ангийг илэрхийлнэ; бодит хүсэлтийн утгад tilde орохгүй.

<!-- PICT-CASES-START -->

| PICT-ээс сонгосон тест | Үүсгэсэн мөр | Setup (данс, үлдэгдэл, лимит) | POST /transfer body | Oracle |
|---|---|---|---|---|
| Happy path | `From=Valid, To=Valid, Amount=Normal, Currency=Same` | ACC001: active, balance=500,000 MNT, daily remaining=500,000 MNT, currency=MNT; ACC002: active, currency=MNT | `{"from":"ACC001","to":"ACC002","amount":50000,"currency":"MNT"}` | HTTP 201, result=OK |
| Нэг алдаа — царцаасан from | `From=~Frozen, To=Valid, Amount=Normal, Currency=Same` | ACC_FROZEN: frozen=true, currency=MNT; ACC002: active, currency=MNT | `{"from":"ACC_FROZEN","to":"ACC002","amount":50000,"currency":"MNT"}` | HTTP 200, result=ERROR_FROZEN |
| Нэг алдаа — amount=0 | `From=Valid, To=Valid, Amount=~Zero, Currency=Different` | ACC001: active, balance=500,000 MNT, daily remaining=500,000 MNT, currency=MNT; ACC002: active, currency=MNT; FX rate 1 USD = 3,500 MNT | `{"from":"ACC001","to":"ACC002","amount":0,"currency":"USD"}` | HTTP 200, result=ERROR_BAD_AMOUNT |

<!-- PICT-CASES-END -->

## Үр дүнгийн нотолгоо

- results/pict-build.txt — PICT-ийн source commit ба CLI usage.
- results/browser-2way.txt, results/browser-3way.txt — browser-ийн 2-way болон 3-way массив.
- results/transfer-nc.txt, results/transfer.txt, results/transfer-neg.txt — шилжүүлгийн гурван моделийн гаралт.
- results/pict-model-counts.json — бодит мөрийн тоонууд.
- results/pict-selected-rows.json — B2 тест кейс болгон хувиргасан PICT мөрүүд.

## Дүгнэлт

Энэ лабораторид Category-Partition болон PICT гэсэн хоёр өөр тест дизайн аргыг нэг банкны шилжүүлгийн жишээн дээр харьцууллаа. Category-Partition нь бизнесийн алдааны утга, тэдгээрийн давуу эрэмбэ, орчны setup-ийг тодорхой тайлбарлахад илүү тохиромжтой байв. PICT нь олон параметрийн pairwise болон 3-way хослолын хамралтыг автоматаар үүсгэхэд илүү үр дүнтэй байлаа. Хамгийн их бодол шаардсан алхам нь үлдэгдэл болон өдрийн лимитийг хөрвүүлсний дараах дүнгээр шалгах далд орчны төлөвүүдийг тодорхойлох байсан. OverBalance болон OverLimit-ийг давхцахгүй fixture-ээр тусгаарласнаар хоёр өөр алдаанд тодорхой oracle өгч чадсан. Давхар алдааны үед from → to → amount гэсэн давуу эрэмбийг сонгосон нь manual спецификацийн хүлээгдэх үр дүнг тогтвортой болгосон. Хязгаарлалтгүй PICT загвар олон алдааг нэг мөрөнд зэрэг оруулж болох тул ганц алдааны шалтгааныг танихад төөрөгдөл үүсгэж болно. transfer.model-ийн IF нөхцөл болон transfer-neg.model-ийн ~ тэмдэглэгээ нь энэ эрсдэлийг өөр өөр аргаар бууруулж байгааг үр дүнгээр харьцуулна. Гар аргын давуу тал нь тестийн бизнесийн утгыг ил тод тайлбарлах, PICT-ийн давуу тал нь хослолын хамралтыг системтэй шалгах юм. Иймээс бодит тест дизайн хийхдээ хоёр аргыг хамтад нь ашиглах нь илүү найдвартай гэж дүгнэв.

## Ажиллуулах команд

Ubuntu дээр git, cmake, g++, make, Python 3 суулгасны дараа репозиториос:

    bash scripts/verify-lab.sh

Скрипт нь PICT source-ийг түр хавтаст clone хийж build хийнэ; PICT source/build нь лабораторийн репозитори руу орохгүй. Дараа нь таван PICT команд ажиллуулж, үр дүнгийн мөрийн тоо болон хослолын хамралтыг шалгаад README-ийн динамик хүснэгтүүдийг шинэчилнэ.

## Git ignore ба ажлын түүх

.gitignore нь .DS_Store, .idea/, pict/, build/ болон Windows pict.exe-г үл тооно. Microsoft PICT-ийн source болон build artifact-ийг репод commit хийхгүй. Энэ репозитори дахь scripts/ нь PICT-ийг reproducible байдлаар build/ажиллуулах, үр дүнгийн хамралтыг шалгах туслах автоматжуулалт бөгөөд шилжүүлгийн API-ийн хэрэгжүүлэлт биш. Ажлын үе шатуудыг тусдаа commit-уудаар хадгалсан.
