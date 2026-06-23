/**
 * YKS sınav yapısı: TYT ve AYT (alanlara göre) ders/soru sayıları.
 * Net hesabı: doğru - yanlış/4 (ÖSYM kuralı, 4 yanlış 1 doğruyu götürür).
 */

export interface SubjectDef {
  key: string;
  label: string;
  max: number; // bu derste toplam soru sayısı
}

export type ExamKind = 'TYT' | 'AYT';

/** TYT bölümleri (toplam 120 soru). */
export const TYT_SECTIONS: SubjectDef[] = [
  { key: 'turkce', label: 'Türkçe', max: 40 },
  { key: 'sosyal', label: 'Sosyal Bilimler', max: 20 },
  { key: 'matematik', label: 'Temel Matematik', max: 40 },
  { key: 'fen', label: 'Fen Bilimleri', max: 20 },
];

/** AYT alanları ve dersleri (her alan toplam ~80 soru). */
export interface AytField {
  id: string;
  label: string;
  sections: SubjectDef[];
}

export const AYT_FIELDS: AytField[] = [
  {
    id: 'sayisal',
    label: 'Sayısal',
    sections: [
      { key: 'ayt_mat', label: 'Matematik', max: 40 },
      { key: 'ayt_fiz', label: 'Fizik', max: 14 },
      { key: 'ayt_kim', label: 'Kimya', max: 13 },
      { key: 'ayt_biy', label: 'Biyoloji', max: 13 },
    ],
  },
  {
    id: 'ea',
    label: 'Eşit Ağırlık',
    sections: [
      { key: 'ayt_mat', label: 'Matematik', max: 40 },
      { key: 'ayt_edb', label: 'Türk Dili ve Edebiyatı', max: 24 },
      { key: 'ayt_tar1', label: 'Tarih-1', max: 10 },
      { key: 'ayt_cog1', label: 'Coğrafya-1', max: 6 },
    ],
  },
  {
    id: 'sozel',
    label: 'Sözel',
    sections: [
      { key: 'ayt_edb', label: 'Türk Dili ve Edebiyatı', max: 24 },
      { key: 'ayt_tar1', label: 'Tarih-1', max: 10 },
      { key: 'ayt_cog1', label: 'Coğrafya-1', max: 6 },
      { key: 'ayt_tar2', label: 'Tarih-2', max: 11 },
      { key: 'ayt_cog2', label: 'Coğrafya-2', max: 11 },
      { key: 'ayt_fel', label: 'Felsefe Grubu', max: 12 },
      { key: 'ayt_din', label: 'Din Kültürü', max: 6 },
    ],
  },
];

/** Bir deneme için ilgili bölüm listesini döndürür. */
export function getSections(kind: ExamKind, fieldId?: string): SubjectDef[] {
  if (kind === 'TYT') return TYT_SECTIONS;
  const field = AYT_FIELDS.find((f) => f.id === fieldId) ?? AYT_FIELDS[0];
  return field.sections;
}

/** Tek ders neti. */
export function calcNet(correct: number, wrong: number): number {
  const net = correct - wrong / 4;
  return Math.round(net * 100) / 100;
}

/** Net'i okunur biçimde göster (gereksiz sıfırları at): 38.75, 40, 12.5. */
export function formatNet(net: number): string {
  return Number.isInteger(net) ? String(net) : String(Math.round(net * 100) / 100);
}

/** Ders anahtarına göre etiket (tüm sınav tiplerinde arar). */
export function subjectLabel(key: string): string {
  const all = [...TYT_SECTIONS, ...AYT_FIELDS.flatMap((f) => f.sections)];
  return all.find((s) => s.key === key)?.label ?? key;
}
