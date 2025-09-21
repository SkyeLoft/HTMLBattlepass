# HTMLBattlepass

A petty little static site that turns a gallery into an escalating prank. Calm language, unhinged purpose: this exists because I wanted to take the mick out of someone, so I made the internet do it for me.

## What it is

HTMLBattlepass is a tiny, front-end-only "battlepass" for images. Visitors click, swipe, or begrudgingly tap through pictures, earn tokens, and burn those tokens to unlock the next, marginally different image. No accounts, no server, just localStorage and decreasing dignity.

This repo is the cleaned-up version — the concept survived; the target remains optional.

## Honest intent

I built this to mock someone. It’s satirical gamification: coax people into doing tiny, pointless work to see a photo that proves nothing. It’s funny, a little mean, and entirely under your control.

## Use cases

- Publicly roast a friend by forcing fans to grind for the “ultimate” embarrassing image.
- Make a gag microsite for a meme, product parody, or inside joke.
- Demonstrate basic gamification mechanics with a darkly comic twist.
- Create a shrine to something mundane and make strangers pay in clicks.

## Features

- Static HTML + vanilla JavaScript — no build, no backend, drop on GitHub Pages, Neocities, or S3.
- Per-view token economy and configurable unlock prices.
- localStorage persistence so the prank lingers.
- JSON-configurable gallery for easy swapping of images, costs, and copy.
- Lightweight and tweakable — meant to be edited, memed, and abused.

## Quick setup

1. Edit assets/ with your images and update config.json to set prices and rewards.
2. Change the copy to name the joke, the target, or keep it anonymous.
3. Deploy index.html to a static host and share the link with the intended victims.
4. Optional: add smug sound effects, a dramatic modal for the “final reveal,” or a faux achievement system.

## Customization ideas

- Make unlock costs painfully slow so people have to grind like it’s a bad mobile game.
- Add absurd achievements (e.g., "Clicked 100 times for no reason") and mock congratulatory copy.
- Lazy-load the top-tier photos and reveal them with a dramatic, mock-epic animation.
- Add a tiny leaderboard stored locally — let the prank become competitive.

## Implementation notes

- Use a site-specific localStorage key to avoid users’ other nonsense colliding.
- Keep images small; lazy-load higher tiers to avoid massive downloads.
- Store gallery data in JSON so anyone can edit the prank without touching JS.

## License

Do what you want. Attribution optional. If you deploy this to publicly roast someone, be a decent human about it — don’t dox, don’t harass, and keep consent in mind.
