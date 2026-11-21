[out:json][timeout:300];
area["ISO3166-1"="ID"][admin_level=2]->.id;
(
  nwr(area.id)["name"~"silat|silek|pencak|penca |padepokan|paguron|paguruan|ipsi|maen pukulan|main pukulan|cimande|cikalong|syahbandar|sabandar|beksi|cingkrik|bandrong|kumango|setia hati|tapak suci|merpati putih|perisai diri|pagar nusa|kera sakti|psht|tunggal hati|perisai putih|satria muda|inti ombak|nur harimau|harimau|sanggar bela diri|perguruan bela diri",i];
  nwr(area.id)["sport"~"pencak_silat|silat",i];
  nwr(area.id)["sport"="martial_arts"];
);
out center tags;
