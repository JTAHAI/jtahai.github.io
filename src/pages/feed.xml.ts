import type { APIRoute } from 'astro';
import { notes } from '../data/content';
export const GET: APIRoute = () => {
  const entries = notes.map(note => `<entry><title>${note.title}</title><id>https://jtahai.github.io/notes/${note.slug}/</id><link href="https://jtahai.github.io/notes/${note.slug}/"/><updated>${note.date}T00:00:00Z</updated><summary>${note.deck}</summary></entry>`).join('');
  return new Response(`<?xml version="1.0" encoding="UTF-8"?><feed xmlns="http://www.w3.org/2005/Atom"><title>Justin Tahai — Systems Notes</title><id>https://jtahai.github.io/</id><updated>2026-09-14T00:00:00Z</updated>${entries}</feed>`, { headers: {'Content-Type':'application/atom+xml; charset=utf-8'} });
};
