/**
 * Share content using Web Share API with clipboard fallback.
 * Returns 'shared' | 'copied' | 'failed'.
 */
export async function shareContent(data: {
  title?: string;
  text?: string;
  url?: string;
}): Promise<'shared' | 'copied' | 'failed'> {
  if (typeof navigator === 'undefined') return 'failed';

  if (navigator.share) {
    try {
      await navigator.share(data);
      return 'shared';
    } catch {
      // User cancelled or API failed — fall through to clipboard
    }
  }

  const textToCopy = data.url || data.text || data.title || '';
  try {
    await navigator.clipboard.writeText(textToCopy);
    return 'copied';
  } catch {
    return 'failed';
  }
}
