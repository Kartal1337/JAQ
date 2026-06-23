import { Inngest } from 'inngest';

export const inngest = new Inngest({ id: 'ai-sdr-assistant' });

// Event names used across the app — keep them centralized.
export const EVENTS = {
  leadsFind: 'campaign/leads.find',
  messagesGenerate: 'campaign/messages.generate',
  campaignLaunch: 'campaign/launch',
  replyReceived: 'reply/received',
} as const;
