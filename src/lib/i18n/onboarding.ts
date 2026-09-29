// Strings for the guided onboarding flow (dashboard/onboarding) and the
// dashboard banner that links to it. Own module, same pattern as
// devices.ts / maintenance.ts. `tr` is typed against `en`.

const en = {
  title: "Get set up",
  subtitle: "Three steps from connecting a panel to a ready-to-submit sell offer.",
  bannerTitle: "Finish setting up SolarFlow",
  bannerSubtitle: "Connect a device, see its failure risk, then forecast prices and build a sell offer.",
  bannerCta: "Continue setup",
  dismiss: "Dismiss",
  stepOf: "Step",
  done: "Done",
  todo: "To do",
  inProgress: "In progress",
  next: "Next",
  back: "Back",
  finish: "Finish",
  goToDashboard: "Go to dashboard",
  loadError: "Could not check your setup status. Make sure the API is running and you are signed in.",

  step1: {
    label: "Connect your panel",
    title: "Share your panel data",
    body: "Register your inverter and give it the device key. Once it pushes telemetry, everything else — failure prediction, price forecasts, sell offers — runs on it.",
    doneMsg: "device(s) connected. You can add more any time from Settings.",
    todoMsg: "No devices yet. Add your first inverter below.",
  },
  step2: {
    label: "See failure risk",
    title: "Predict when your panel will fail",
    body: "With telemetry flowing, the PV fault model scores each device's risk over the next few hours and flags what needs attention.",
    run: "Run assessment now",
    running: "Assessing…",
    doneMsg: "device(s) assessed. Highest current risk:",
    todoMsg: "No assessment yet. Run one once a device has sent telemetry.",
    openPage: "Open predictive maintenance",
    needDevice: "Connect a device first.",
  },
  step3: {
    label: "Forecast prices & sell",
    title: "PTF forecast and your sell offer",
    body: "We forecast tomorrow's day-ahead clearing price (PTF) hour by hour, then turn your expected surplus into a priced sell offer before the 12:30 gate.",
    priceRows: "price rows loaded",
    noPrices: "No market prices yet — sync from EPİAŞ on the Market page.",
    openPage: "Open market & offers",
    doneMsg: "You're all set. Review your forecast and offer on the Market page.",
  },
};

const tr: typeof en = {
  title: "Kurulumu tamamla",
  subtitle: "Panel bağlamaktan gönderilmeye hazır satış teklifine üç adım.",
  bannerTitle: "SolarFlow kurulumunu bitir",
  bannerSubtitle: "Bir cihaz bağla, arıza riskini gör, sonra fiyat tahmini yap ve satış teklifi oluştur.",
  bannerCta: "Kuruluma devam et",
  dismiss: "Kapat",
  stepOf: "Adım",
  done: "Tamam",
  todo: "Yapılacak",
  inProgress: "Sürüyor",
  next: "İleri",
  back: "Geri",
  finish: "Bitir",
  goToDashboard: "Panele git",
  loadError: "Kurulum durumu kontrol edilemedi. API'nin çalıştığından ve oturum açtığınızdan emin olun.",

  step1: {
    label: "Panelini bağla",
    title: "Panel verini paylaş",
    body: "İnverterini kaydet ve cihaz anahtarını ona ver. Telemetri göndermeye başlayınca geri kalan her şey — arıza tahmini, fiyat tahminleri, satış teklifleri — bunun üzerinde çalışır.",
    doneMsg: "cihaz bağlı. Ayarlar'dan istediğin zaman ekleyebilirsin.",
    todoMsg: "Henüz cihaz yok. İlk inverterini aşağıya ekle.",
  },
  step2: {
    label: "Arıza riskini gör",
    title: "Panelinin ne zaman arızalanacağını tahmin et",
    body: "Telemetri akarken PV arıza modeli her cihazın önümüzdeki birkaç saatteki riskini puanlar ve dikkat gerektirenleri işaretler.",
    run: "Şimdi değerlendir",
    running: "Değerlendiriliyor…",
    doneMsg: "cihaz değerlendirildi. Şu anki en yüksek risk:",
    todoMsg: "Henüz değerlendirme yok. Bir cihaz telemetri gönderince çalıştır.",
    openPage: "Kestirimci bakımı aç",
    needDevice: "Önce bir cihaz bağla.",
  },
  step3: {
    label: "Fiyat tahmini & sat",
    title: "PTF tahmini ve satış teklifin",
    body: "Yarının gün öncesi takas fiyatını (PTF) saat saat tahmin ederiz, sonra beklenen fazlanı 12:30 kapanışından önce fiyatlı bir satış teklifine dönüştürürüz.",
    priceRows: "fiyat satırı yüklendi",
    noPrices: "Henüz piyasa fiyatı yok — Piyasa sayfasından EPİAŞ ile eşitle.",
    openPage: "Piyasa & teklifleri aç",
    doneMsg: "Hazırsın. Tahminini ve teklifini Piyasa sayfasında incele.",
  },
};

export const onboardingText = { en, tr };
