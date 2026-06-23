import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  TextInput,
  View,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Txt } from '@/components/Txt';
import { Button } from '@/components/Button';
import { useStore } from '@/store/useStore';
import { tr } from '@/locale/tr';
import { palette, radius, spacing } from '@/theme/theme';
import { complete, COACH_SYSTEM_PROMPT, type ChatMessage } from '@/lib/ai';

interface UIMessage extends ChatMessage {
  id: string;
}

type QuickAction = keyof typeof tr.chat.quickActions;

export default function ChatScreen() {
  const settings = useStore((s) => s.settings);
  const sessions = useStore((s) => s.sessions);

  const { draft } = useLocalSearchParams<{ draft?: string }>();
  const activeTopic = sessions[0]?.topic;
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [input, setInput] = useState('');

  // Başka ekrandan gelen hazır metni (ör. deneme analizi) giriş alanına koy
  useEffect(() => {
    if (draft) setInput(draft);
  }, [draft]);
  const [busy, setBusy] = useState(false);
  const listRef = useRef<FlatList<UIMessage>>(null);
  const abortRef = useRef<AbortController | null>(null);

  const sysPrompt = useMemo(() => {
    let p = COACH_SYSTEM_PROMPT;
    if (activeTopic) {
      p += `\n\nÖğrencinin şu anki çalışma konusu: "${activeTopic}". İlgili olduğunda buna referans verebilirsin.`;
    }
    return p;
  }, [activeTopic]);

  const scrollToEnd = () =>
    setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 60);

  const send = useCallback(
    async (text: string) => {
      const content = text.trim();
      if (!content || busy) return;
      if (!settings.apiKey) return;

      const userMsg: UIMessage = { id: `u${Date.now()}`, role: 'user', content };
      const assistantId = `a${Date.now()}`;
      const assistantMsg: UIMessage = { id: assistantId, role: 'assistant', content: '' };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setInput('');
      setBusy(true);
      scrollToEnd();

      // Sağlayıcıya gönderilecek konuşma geçmişi (UI id'leri olmadan)
      const history: ChatMessage[] = [
        { role: 'system', content: sysPrompt },
        ...messages.map(({ role, content }) => ({ role, content })),
        { role: 'user', content },
      ];

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        await complete({
          provider: settings.provider,
          apiKey: settings.apiKey,
          messages: history,
          signal: controller.signal,
          onToken: (chunk) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, content: m.content + chunk } : m
              )
            );
          },
        });
      } catch (e) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId && !m.content
              ? { ...m, content: tr.chat.errorGeneric }
              : m
          )
        );
      } finally {
        setBusy(false);
        abortRef.current = null;
        scrollToEnd();
      }
    },
    [busy, settings.apiKey, settings.provider, messages, sysPrompt]
  );

  const runQuickAction = (action: QuickAction) => {
    const subject = input.trim() || activeTopic || 'çalıştığım konu';
    const prompts: Record<QuickAction, string> = {
      summarize: `"${subject}" konusunu kısa ve anlaşılır şekilde özetler misin? Önemli noktaları madde madde yaz.`,
      ask: `"${subject}" konusundan bana 1 tane düşündürücü soru sor, cevabımı bekle.`,
      quiz: `"${subject}" konusundan 5 soruluk kısa bir test hazırla (şıklı). Cevap anahtarını en sona koy.`,
      solve: `Şu soruyu/konuyu adım adım, her adımı açıklayarak çöz: "${subject}"`,
    };
    send(prompts[action]);
  };

  // API anahtarı yoksa yönlendirme ekranı
  if (!settings.apiKey) {
    return (
      <SafeAreaView style={styles.safe} edges={['top']}>
        <View style={styles.emptyWrap}>
          <Txt style={styles.emptyEmoji}>🔑</Txt>
          <Txt variant="h2" weight="bold" center>
            {tr.chat.title}
          </Txt>
          <Txt variant="body" tone="muted" center style={{ marginTop: spacing.md }}>
            {tr.chat.noApiKey}
          </Txt>
          <Button
            label={tr.chat.goToSettings}
            icon="settings"
            onPress={() => router.push('/(tabs)/profile')}
            style={{ marginTop: spacing.xl, alignSelf: 'stretch' }}
          />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 0}
      >
        {/* Başlık */}
        <View style={styles.header}>
          <View style={styles.avatar}>
            <Txt style={{ fontSize: 22 }}>🤖</Txt>
          </View>
          <View style={{ flex: 1 }}>
            <Txt variant="h3" weight="bold">
              {tr.chat.title}
            </Txt>
            <Txt variant="tiny" tone="muted">
              {activeTopic
                ? `${tr.chat.sessionContext}: ${activeTopic}`
                : tr.chat.subtitle}
            </Txt>
          </View>
        </View>

        {/* Mesajlar */}
        {messages.length === 0 ? (
          <View style={styles.emptyWrap}>
            <Txt style={styles.emptyEmoji}>💬</Txt>
            <Txt variant="h3" weight="bold" center>
              {tr.chat.emptyTitle}
            </Txt>
            <Txt variant="body" tone="muted" center style={{ marginTop: spacing.sm }}>
              {tr.chat.emptySubtitle}
            </Txt>
          </View>
        ) : (
          <FlatList
            ref={listRef}
            data={messages}
            keyExtractor={(m) => m.id}
            contentContainerStyle={styles.listContent}
            showsVerticalScrollIndicator={false}
            renderItem={({ item }) => <Bubble message={item} busy={busy} />}
            onContentSizeChange={scrollToEnd}
          />
        )}

        {/* Hızlı aksiyonlar */}
        <View style={styles.quickRow}>
          {(Object.keys(tr.chat.quickActions) as QuickAction[]).map((a) => (
            <Pressable
              key={a}
              style={styles.quickChip}
              onPress={() => runQuickAction(a)}
              disabled={busy}
            >
              <Txt variant="tiny" weight="semibold" tone="primary">
                {tr.chat.quickActions[a]}
              </Txt>
            </Pressable>
          ))}
        </View>

        {/* Giriş alanı */}
        <View style={styles.inputBar}>
          <TextInput
            value={input}
            onChangeText={setInput}
            placeholder={tr.chat.placeholder}
            placeholderTextColor={palette.textFaint}
            style={styles.chatInput}
            multiline
            onSubmitEditing={() => send(input)}
          />
          <Pressable
            style={[styles.sendBtn, (busy || !input.trim()) && styles.sendBtnOff]}
            onPress={() => send(input)}
            disabled={busy || !input.trim()}
          >
            <Ionicons name={busy ? 'ellipsis-horizontal' : 'send'} size={20} color={palette.white} />
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function Bubble({ message, busy }: { message: UIMessage; busy: boolean }) {
  const isUser = message.role === 'user';
  const isTyping = !isUser && message.content === '' && busy;
  return (
    <View style={[styles.bubbleRow, isUser ? styles.rowEnd : styles.rowStart]}>
      <View style={[styles.bubble, isUser ? styles.userBubble : styles.aiBubble]}>
        <Txt variant="body" tone={isUser ? 'inverse' : 'default'} style={{ lineHeight: 22 }}>
          {isTyping ? tr.chat.thinking : message.content}
        </Txt>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: palette.bg },
  flex: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: palette.border,
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: radius.full,
    backgroundColor: palette.surface,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: palette.border,
  },
  emptyWrap: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  emptyEmoji: { fontSize: 56, marginBottom: spacing.md },
  listContent: { padding: spacing.lg, gap: spacing.md },
  bubbleRow: { flexDirection: 'row' },
  rowEnd: { justifyContent: 'flex-end' },
  rowStart: { justifyContent: 'flex-start' },
  bubble: { maxWidth: '84%', padding: spacing.md, borderRadius: radius.lg },
  userBubble: { backgroundColor: palette.primary, borderBottomRightRadius: 4 },
  aiBubble: {
    backgroundColor: palette.surface,
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: palette.border,
  },
  quickRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  quickChip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.full,
    backgroundColor: palette.primary + '1A',
    borderWidth: 1,
    borderColor: palette.primary + '44',
  },
  inputBar: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.sm,
    paddingBottom: spacing.md,
    borderTopWidth: 1,
    borderTopColor: palette.border,
  },
  chatInput: {
    flex: 1,
    maxHeight: 120,
    backgroundColor: palette.surface,
    borderRadius: radius.lg,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    color: palette.text,
    fontSize: 16,
    borderWidth: 1,
    borderColor: palette.border,
  },
  sendBtn: {
    width: 48,
    height: 48,
    borderRadius: radius.full,
    backgroundColor: palette.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendBtnOff: { opacity: 0.4 },
});
