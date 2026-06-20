/**
 * Motivasyon sözleri (gençlere hitap eden, Türkçe).
 * Günün sözü her gün deterministik olarak seçilir.
 */

export type Quote = { text: string; emoji: string };

export const quotes: Quote[] = [
  { text: 'Bugün yapacağın küçük bir adım, yarının büyük farkı.', emoji: '🌟' },
  { text: 'Disiplin, motivasyonun bittiği yerde devam etmektir.', emoji: '💪' },
  { text: 'Zor gelen şey, seni güçlendiren şeydir.', emoji: '🔥' },
  { text: 'Bir sonraki soru, hedefine bir adım daha yakın.', emoji: '🎯' },
  { text: 'Pes etme; en karanlık an, şafaktan hemen öncesidir.', emoji: '🌅' },
  { text: 'Bugünün emeği, yarının diploması.', emoji: '🎓' },
  { text: 'Küçük tekrarlar, büyük başarıları getirir.', emoji: '📈' },
  { text: 'Sen yapabilirsin, sadece başla.', emoji: '🚀' },
  { text: 'Odaklan, gerisi gelir.', emoji: '🧠' },
  { text: 'Her gün biraz daha iyi. İşte tek kural bu.', emoji: '⭐' },
  { text: 'Hayallerin, çalışmanın diğer adı.', emoji: '✨' },
  { text: 'Yorulduğunda durma, bitirdiğinde dur.', emoji: '🏁' },
  { text: 'Şampiyonlar antrenmanda yorulanlardır.', emoji: '🏆' },
  { text: 'Bir pomodoro daha, bir adım daha öne.', emoji: '🍅' },
];

/** Tarihe göre deterministik günün sözü. */
export function getQuoteOfTheDay(date = new Date()): Quote {
  const dayIndex = Math.floor(date.getTime() / (1000 * 60 * 60 * 24));
  return quotes[dayIndex % quotes.length];
}

/** Pomodoro sonrası rastgele kısa motivasyon. */
export const postSessionCheers: string[] = [
  'Efsane! Bir pomodoro daha cebinde 🔥',
  'Beynin teşekkür ediyor 🧠✨',
  'İşte bu! Seri devam ediyor 💪',
  'Harikasın, mola hak ettin 🧘',
  'Adım adım hedefe yürüyorsun 🎯',
  'Bu tempoyla YKS senin olur 🚀',
];
