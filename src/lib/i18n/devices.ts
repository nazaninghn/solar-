// Strings for the Connected Devices panel (settings > devices), per locale.
// Kept in its own module like maintenance.ts / market.ts so the panel only
// depends on the committed LanguageContext `locale`. `tr` is typed against
// `en`, so a missing Turkish key fails the build.

const en = {
  dateLocale: "en-US",
  title: "Connected devices",
  subtitle:
    "Register your inverters, batteries and meters. Once a device sends telemetry, it powers failure prediction, forecasting and market offers.",
  add: "Add device",
  adding: "Adding…",
  cancel: "Cancel",
  empty: "No devices yet. Add your first inverter to start sharing panel data.",
  loadError: "Could not load devices. Check that the API is running and you are signed in.",

  // Table / rows
  name: "Name",
  type: "Type",
  status: "Status",
  lastSeen: "Last seen",
  never: "never",
  actions: "Actions",
  testConnection: "Test",
  testing: "Testing…",
  regenerate: "New key",
  remove: "Remove",
  confirmRemove: "Remove this device? Telemetry it already sent is kept, but it can no longer connect.",

  // Statuses (device.status from the backend)
  statuses: {
    online: "Online",
    offline: "Offline",
    error: "Error",
    pending: "Pending",
    unknown: "Unknown",
  } as Record<string, string>,

  // Add form
  formTitle: "Register a device",
  fieldName: "Display name",
  fieldNamePlaceholder: "Rooftop inverter A",
  fieldType: "Device type",
  fieldManufacturer: "Manufacturer",
  fieldModel: "Model",
  fieldSerial: "Serial number",
  fieldConnection: "Connection",
  optional: "optional",
  deviceTypes: {
    inverter: "Inverter (PV)",
    battery: "Battery",
    meter: "Meter",
    gateway: "Gateway",
  } as Record<string, string>,
  connectionTypes: {
    api: "API push (device key)",
    modbus: "Modbus TCP",
    mqtt: "MQTT",
  } as Record<string, string>,

  // Device key reveal (shown once)
  keyTitle: "Device key — copy it now",
  keyHint:
    "This is the only time the key is shown. The device uses it to authenticate when pushing telemetry. Store it somewhere safe.",
  copy: "Copy",
  copied: "Copied",
  keyDone: "I've saved it",
  regenerateWarn:
    "The old key stops working immediately. Any device still using it will fail to connect until updated.",

  testOk: "Connected",
  testFail: "No connection",
  latency: "latency",
};

const tr: typeof en = {
  dateLocale: "tr-TR",
  title: "Bağlı cihazlar",
  subtitle:
    "İnverterlerinizi, bataryalarınızı ve sayaçlarınızı kaydedin. Bir cihaz telemetri göndermeye başlayınca arıza tahmini, fiyat tahmini ve piyasa tekliflerini besler.",
  add: "Cihaz ekle",
  adding: "Ekleniyor…",
  cancel: "İptal",
  empty: "Henüz cihaz yok. Panel verisi paylaşmaya başlamak için ilk inverterinizi ekleyin.",
  loadError: "Cihazlar yüklenemedi. API'nin çalıştığından ve oturum açtığınızdan emin olun.",

  name: "Ad",
  type: "Tür",
  status: "Durum",
  lastSeen: "Son görülme",
  never: "hiç",
  actions: "İşlemler",
  testConnection: "Test",
  testing: "Test ediliyor…",
  regenerate: "Yeni anahtar",
  remove: "Kaldır",
  confirmRemove: "Bu cihaz kaldırılsın mı? Gönderdiği telemetri saklanır ama artık bağlanamaz.",

  statuses: {
    online: "Çevrimiçi",
    offline: "Çevrimdışı",
    error: "Hata",
    pending: "Beklemede",
    unknown: "Bilinmiyor",
  } as Record<string, string>,

  formTitle: "Cihaz kaydet",
  fieldName: "Görünen ad",
  fieldNamePlaceholder: "Çatı inverteri A",
  fieldType: "Cihaz türü",
  fieldManufacturer: "Üretici",
  fieldModel: "Model",
  fieldSerial: "Seri numarası",
  fieldConnection: "Bağlantı",
  optional: "isteğe bağlı",
  deviceTypes: {
    inverter: "İnverter (PV)",
    battery: "Batarya",
    meter: "Sayaç",
    gateway: "Ağ geçidi",
  } as Record<string, string>,
  connectionTypes: {
    api: "API push (cihaz anahtarı)",
    modbus: "Modbus TCP",
    mqtt: "MQTT",
  } as Record<string, string>,

  keyTitle: "Cihaz anahtarı — şimdi kopyalayın",
  keyHint:
    "Anahtar yalnızca bir kez gösterilir. Cihaz telemetri gönderirken kimlik doğrulaması için bunu kullanır. Güvenli bir yerde saklayın.",
  copy: "Kopyala",
  copied: "Kopyalandı",
  keyDone: "Kaydettim",
  regenerateWarn:
    "Eski anahtar hemen çalışmayı durdurur. Onu kullanan cihazlar güncellenene kadar bağlanamaz.",

  testOk: "Bağlandı",
  testFail: "Bağlantı yok",
  latency: "gecikme",
};

export const devicesText = { en, tr };
