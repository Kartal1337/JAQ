/**
 * email.ts — outbound sending. MVP uses Resend (simplest API + inbound
 * support). To send from a user's own Gmail, swap this for the Gmail API
 * using sending_accounts.oauth_refresh_token — the call sites only depend on
 * sendEmail().
 *
 * If RESEND_API_KEY is unset, logs instead of sending so you can test the
 * full queue locally without burning sends.
 */
import { Resend } from 'resend';

export interface SendEmailInput {
  from: string;          // verified sender, e.g. "Jane <jane@yourdomain.com>"
  to: string;
  subject: string;
  body: string;          // plain text; newlines become <br> in html
  replyTo?: string;
  headers?: Record<string, string>;
}

export interface SendEmailResult {
  id: string;
  status: 'sent' | 'logged';
}

export async function sendEmail(input: SendEmailInput): Promise<SendEmailResult> {
  const key = process.env.RESEND_API_KEY;
  if (!key) {
    console.log('[email:dev] would send', { to: input.to, subject: input.subject });
    return { id: `dev-${Date.now()}`, status: 'logged' };
  }

  const resend = new Resend(key);
  const { data, error } = await resend.emails.send({
    from: input.from,
    to: input.to,
    subject: input.subject,
    replyTo: input.replyTo,
    headers: input.headers,
    text: input.body,
    html: input.body.replace(/\n/g, '<br>'),
  });

  if (error) throw new Error(`Resend error: ${error.message}`);
  return { id: data!.id, status: 'sent' };
}
