/**
 * The Dragon's Cave - A Fantasy Adventure
 *
 * A classic fantasy story with multiple paths and endings.
 * Features: combat choices, treasure hunting, moral decisions
 */

import type { Story } from '../engine/types';

export const dragonsCave: Story = {
  id: 'dragons-cave',
  title: "The Dragon's Cave",
  description: "You are a brave adventurer seeking the legendary Dragon's Hoard. Will you claim the treasure, befriend the dragon, or meet a fiery end?",
  theme: 'fantasy',
  startNodeId: 'start',
  nodes: {
    // === ACT 1: The Journey Begins ===
    'start': {
      id: 'start',
      title: 'The Village of Millbrook',
      content: `You stand at the edge of Millbrook, a small village nestled in the shadow of the Thornback Mountains. For generations, tales have been told of a dragon who guards an immense treasure in a cave high above.

Many adventurers have sought the hoard. None have returned.

But you are different. Armed with your wits and courage, you're determined to succeed where others have failed. The mountain path stretches before you, disappearing into the morning mist.`,
      choices: [
        { id: 'take-sword', text: 'Take the ancient sword from the village shrine', nextNodeId: 'shrine' },
        { id: 'visit-sage', text: 'Visit the old sage for wisdom', nextNodeId: 'sage' },
        { id: 'go-direct', text: 'Head straight for the mountain', nextNodeId: 'mountain-base' },
      ],
    },

    'shrine': {
      id: 'shrine',
      title: 'The Village Shrine',
      content: `The shrine is ancient, covered in moss and forgotten prayers. At its center rests a sword of remarkable craftsmanship—the Blade of Dawn, they call it.

The village elder watches as you approach. "That blade was forged to slay the dragon," she says. "But be warned: it carries a curse. Those who wield it against the innocent will find their own hearts turned to stone."

You take the sword. It feels warm in your grip, almost alive.`,
      choices: [
        { id: 'sage-after-sword', text: 'Now visit the sage', nextNodeId: 'sage-with-sword' },
        { id: 'mountain-with-sword', text: 'Head to the mountain', nextNodeId: 'mountain-base' },
      ],
      effect: (state) => ({ ...state, variables: { ...state.variables, hasSword: true } }),
    },

    'sage': {
      id: 'sage',
      title: "The Sage's Hut",
      content: `The sage lives in a crooked hut at the village edge. She's impossibly old, with eyes that seem to see through time itself.

"Ah, another dragon hunter," she rasps. "Tell me, young one, do you seek gold... or glory?"

She pauses, studying you. "The dragon is ancient and wise. Not all treasures are made of gold, and not all victories require bloodshed. Remember this: speak the dragon's true name, and you may find an ally instead of an enemy."

She whispers something in your ear—a word in a language older than the mountains themselves.`,
      choices: [
        { id: 'shrine-after-sage', text: 'Visit the shrine for the sword', nextNodeId: 'shrine' },
        { id: 'mountain-after-sage', text: 'Head to the mountain', nextNodeId: 'mountain-base' },
      ],
      effect: (state) => ({ ...state, variables: { ...state.variables, knowsName: true } }),
    },

    'sage-with-sword': {
      id: 'sage-with-sword',
      title: "The Sage's Warning",
      content: `The sage's eyes widen when she sees the Blade of Dawn at your hip.

"You carry the cursed blade," she says quietly. "It will give you power against the dragon, but at what cost? The blade hungers for dragon blood—it may not give you a choice in the end."

She tells you the dragon's true name anyway, whispering it like a secret. "Perhaps you will find another way. Perhaps."`,
      choices: [
        { id: 'to-mountain', text: 'Head to the mountain', nextNodeId: 'mountain-base' },
      ],
      effect: (state) => ({ ...state, variables: { ...state.variables, knowsName: true, sageWarning: true } }),
    },

    // === ACT 2: The Mountain ===
    'mountain-base': {
      id: 'mountain-base',
      title: 'The Mountain Path',
      content: `The path up Thornback Mountain is treacherous. Loose stones threaten to send you tumbling with every step, and the wind howls through the crags like a wounded beast.

Halfway up, you come to a fork in the path. To the left, a narrow trail winds along a cliff face—dangerous, but direct. To the right, a cave entrance promises shelter but leads into unknown darkness.`,
      choices: [
        { id: 'cliff-path', text: 'Take the cliff path', nextNodeId: 'cliff-path' },
        { id: 'cave-path', text: 'Enter the cave', nextNodeId: 'cave-path' },
      ],
    },

    'cliff-path': {
      id: 'cliff-path',
      title: 'The Cliff Path',
      content: `The cliff path is every bit as dangerous as it looks. Wind tears at your clothes, and the rock crumbles beneath your feet. But you press on, one careful step at a time.

Suddenly, a section of the path gives way! You throw yourself forward, barely catching the edge. As you pull yourself up, you see something glinting in a crevice—a golden amulet, lost by some previous adventurer.

You pocket it and continue, eventually reaching a ledge overlooking the dragon's cave entrance.`,
      choices: [
        { id: 'enter-dragon-lair', text: 'Enter the cave', nextNodeId: 'dragon-lair-entrance' },
        { id: 'observe-first', text: 'Observe from hiding first', nextNodeId: 'observe-dragon' },
      ],
      effect: (state) => ({ ...state, variables: { ...state.variables, hasAmulet: true } }),
    },

    'cave-path': {
      id: 'cave-path',
      title: 'The Dark Tunnels',
      content: `The cave is pitch black, but you press forward, one hand on the wall. Strange sounds echo in the darkness—dripping water, the scuttle of unseen creatures, and something else... breathing?

You round a corner and find yourself face-to-face with a young dragon, no bigger than a horse. It's clearly not THE dragon, but one of its offspring. It hisses, smoke curling from its nostrils.`,
      choices: [
        { id: 'fight-young-dragon', text: 'Draw your weapon and fight', nextNodeId: 'fight-young-dragon' },
        { id: 'calm-young-dragon', text: 'Try to calm it with gentle words', nextNodeId: 'calm-young-dragon' },
        { id: 'flee-young-dragon', text: 'Run back the way you came', nextNodeId: 'flee-tunnels' },
      ],
    },

    'fight-young-dragon': {
      id: 'fight-young-dragon',
      title: 'Battle in the Dark',
      content: `The young dragon lunges, but you're faster. Your blade finds its mark, and the creature falls with a pitiful cry.

As it dies, you hear a terrible roar echo through the tunnels—the parent dragon has heard its child's death cry. The walls shake with its fury.

You've made a powerful enemy. But the path ahead is now clear.`,
      choices: [
        { id: 'continue-angry', text: 'Continue to the dragon\'s lair', nextNodeId: 'dragon-lair-angry' },
      ],
      effect: (state) => ({ ...state, variables: { ...state.variables, killedYoung: true } }),
    },

    'calm-young-dragon': {
      id: 'calm-young-dragon',
      title: 'An Unexpected Friend',
      content: `You lower your weapon and speak softly. The young dragon tilts its head, curious. Slowly, you reach out your hand.

To your amazement, it nuzzles against your palm like a cat. It seems to recognize something in you—perhaps kindness, perhaps something more.

The young dragon leads you through the tunnels, guiding you safely to the main lair. It chirps happily, clearly proud to show you the way.`,
      choices: [
        { id: 'follow-friend', text: 'Follow your new friend', nextNodeId: 'dragon-lair-peaceful' },
      ],
      effect: (state) => ({ ...state, variables: { ...state.variables, friendedYoung: true } }),
    },

    'flee-tunnels': {
      id: 'flee-tunnels',
      title: 'A Hasty Retreat',
      content: `You turn and run, the young dragon's flames licking at your heels. You burst out of the cave and scramble up the cliff path instead.

Your heart pounds as you reach the ledge above the dragon's lair. You survived, but the memory of those flames will haunt you.`,
      choices: [
        { id: 'enter-after-flee', text: 'Enter the dragon\'s cave', nextNodeId: 'dragon-lair-entrance' },
      ],
    },

    'observe-dragon': {
      id: 'observe-dragon',
      title: 'The Watcher',
      content: `From your hiding spot, you observe the cave entrance. After an hour, the dragon emerges—and your breath catches.

It's magnificent. Scales like molten copper, eyes like pools of amber fire. But it's also clearly ancient, its movements slow and deliberate. And there, clutched in one claw... a book?

The dragon settles on a rocky outcrop and begins to read, turning pages with surprising delicacy. This is not the mindless beast of legend.`,
      choices: [
        { id: 'approach-reading', text: 'Approach the reading dragon peacefully', nextNodeId: 'approach-peaceful' },
        { id: 'sneak-past', text: 'Sneak into the cave while it\'s distracted', nextNodeId: 'sneak-into-lair' },
      ],
    },

    // === ACT 3: The Dragon's Lair ===
    'dragon-lair-entrance': {
      id: 'dragon-lair-entrance',
      title: "The Dragon's Lair",
      content: `You enter the cave, and the sight takes your breath away. Mountains of gold coins, jeweled crowns, ancient artifacts—wealth beyond imagination.

And there, atop the hoard, lies the dragon. Its eyes open as you enter, fixing you with an ancient, knowing gaze.

"Another treasure seeker," it rumbles, its voice like grinding boulders. "Tell me, small one, what makes you different from all the others who came before?"`,
      choices: [
        { id: 'demand-treasure', text: '"I\'ve come for your treasure!"', nextNodeId: 'demand-battle' },
        { id: 'speak-true-name', text: 'Speak the dragon\'s true name', nextNodeId: 'speak-name', condition: (state) => state.variables.knowsName === true },
        { id: 'ask-question', text: '"What happened to the others?"', nextNodeId: 'dragon-story' },
      ],
    },

    'dragon-lair-angry': {
      id: 'dragon-lair-angry',
      title: 'The Enraged Dragon',
      content: `You emerge into the dragon's lair to find chaos. Gold is scattered everywhere, and the dragon paces furiously, smoke billowing from its nostrils.

It spots you and ROARS, flames erupting from its maw. "YOU! You killed my child!"

There will be no negotiation now. Only battle.`,
      choices: [
        { id: 'battle-angry', text: 'Fight the enraged dragon', nextNodeId: 'final-battle-hard' },
      ],
    },

    'dragon-lair-peaceful': {
      id: 'dragon-lair-peaceful',
      title: 'A Warm Welcome',
      content: `The young dragon leads you into the lair, chirping excitedly. The great dragon looks up from its reading, surprised but not alarmed.

"Well, well," it says, a hint of warmth in its ancient voice. "My child has brought me a guest. You must be remarkable indeed to have earned such trust."

It gestures with one great claw. "Come, sit. Let us talk before we discuss the matter of treasure."`,
      choices: [
        { id: 'talk-peaceful', text: 'Sit and talk with the dragon', nextNodeId: 'dragon-conversation' },
        { id: 'betray-trust', text: 'Use this moment to attack', nextNodeId: 'betrayal-attempt' },
      ],
    },

    'approach-peaceful': {
      id: 'approach-peaceful',
      title: 'The Approach',
      content: `You step out from hiding and walk toward the dragon, hands raised peacefully. It looks up from its book, surprised but not hostile.

"A human who does not attack on sight," it muses. "How... unusual. I am Verathrax, though you may have heard other names for me. What brings you to my mountain, little one?"`,
      choices: [
        { id: 'honest-answer', text: '"I came seeking treasure, but now I\'m curious about you."', nextNodeId: 'dragon-conversation' },
        { id: 'use-name', text: 'Speak its true name', nextNodeId: 'speak-name-peaceful', condition: (state) => state.variables.knowsName === true },
      ],
    },

    'sneak-into-lair': {
      id: 'sneak-into-lair',
      title: 'The Thief',
      content: `You slip into the lair while the dragon reads outside. The treasure is right there—mountains of gold, ancient artifacts, priceless gems.

You fill your pockets, your bag, grabbing everything you can carry. You're going to be rich!

Then you hear wings. The dragon lands at the cave entrance, blocking your escape, its eyes gleaming with cold fury.

"Thief," it hisses.`,
      choices: [
        { id: 'fight-caught', text: 'Fight your way out', nextNodeId: 'final-battle-hard' },
        { id: 'beg-mercy', text: 'Drop everything and beg for mercy', nextNodeId: 'mercy-plea' },
      ],
    },

    // === Conversation Branch ===
    'dragon-conversation': {
      id: 'dragon-conversation',
      title: 'Tales of Ages Past',
      content: `You talk for hours. The dragon—Verathrax—tells you of ages past, of when dragons and humans lived in peace, before greed and fear drove them apart.

"I do not hate your kind," Verathrax says. "I am simply... tired. Tired of being hunted. Tired of watching the brave and foolish die. The treasure means nothing to me—it is merely what humans expect a dragon to guard."

The dragon looks at you with ancient, weary eyes. "What do you truly want, adventurer?"`,
      choices: [
        { id: 'want-peace', text: '"I want to restore peace between our peoples."', nextNodeId: 'peace-ending' },
        { id: 'want-treasure', text: '"I still want the treasure. But perhaps we can make a deal?"', nextNodeId: 'deal-ending' },
        { id: 'want-nothing', text: '"I no longer want anything. This journey has changed me."', nextNodeId: 'wisdom-ending' },
      ],
    },

    'dragon-story': {
      id: 'dragon-story',
      title: 'The Fate of Heroes',
      content: `The dragon's laugh echoes through the cavern. "The others? They attacked. They schemed. They pleaded. In the end, they all became the same thing."

It gestures to a corner of the lair, where armor and weapons lie in a pile, some still bearing scorch marks.

"I gave each one a chance to leave. None took it. Will you be different?"`,
      choices: [
        { id: 'choose-leave', text: 'Leave peacefully', nextNodeId: 'leave-empty' },
        { id: 'choose-fight', text: 'Draw your weapon', nextNodeId: 'final-battle-fair' },
        { id: 'choose-talk', text: '"Why do you let them attack? Why not stop them?"', nextNodeId: 'dragon-conversation' },
      ],
    },

    // === Battle Outcomes ===
    'demand-battle': {
      id: 'demand-battle',
      title: 'The Challenge',
      content: `"Bold," the dragon says, rising to its full height. Fire crackles at the back of its throat. "Very well, treasure seeker. Earn your gold... if you can."

The battle begins!`,
      choices: [
        { id: 'fight-standard', text: 'Fight the dragon', nextNodeId: 'final-battle-fair' },
      ],
    },

    'final-battle-fair': {
      id: 'final-battle-fair',
      title: 'Battle for the Hoard',
      content: `The fight is brutal. Fire and steel clash as you dodge the dragon's flames and strike at its scales. The beast is powerful, but old—its movements predictable.

With a final, desperate lunge, your blade finds its mark. The dragon falls with a sound like thunder.

You stand victorious, surrounded by unimaginable wealth. But as the light fades from the dragon's eyes, you feel only emptiness.`,
      choices: [
        { id: 'take-treasure-victory', text: 'Take the treasure and leave', nextNodeId: 'victory-hollow' },
      ],
      effect: (state) => ({ ...state, variables: { ...state.variables, killedDragon: true } }),
    },

    'final-battle-hard': {
      id: 'final-battle-hard',
      title: 'The Furious Battle',
      content: `This is no ordinary fight. The dragon is enraged, its flames hotter, its strikes faster. You're outmatched.

A claw catches you across the chest. You fall, and the world goes dark...

You wake to find yourself alive, but badly wounded, outside the cave. The dragon has spared you—barely.

"Leave," its voice echoes from within. "And never return."`,
      choices: [
        { id: 'retreat-defeated', text: 'Limp back to the village', nextNodeId: 'defeat-ending' },
      ],
    },

    'betrayal-attempt': {
      id: 'betrayal-attempt',
      title: 'Betrayal',
      content: `You draw your weapon and strike at the dragon's unprotected neck. But the young dragon is faster—it leaps between you, taking the blow meant for its parent.

The great dragon's roar of grief and fury shakes the mountain itself. You don't stand a chance.

The last thing you see is fire.`,
      choices: [],
      isEnding: true,
      endingType: 'defeat',
    },

    // === Name Branch ===
    'speak-name': {
      id: 'speak-name',
      title: 'The True Name',
      content: `You speak the word the sage taught you—the dragon's true name, in the language of creation itself.

The dragon's eyes widen. For a moment, it is utterly still. Then it bows its great head.

"You know my name," it says softly. "The first human in a thousand years. Tell me... what do you want?"`,
      choices: [
        { id: 'name-peace', text: '"I want peace between our peoples."', nextNodeId: 'peace-ending' },
        { id: 'name-wisdom', text: '"I want to learn from you."', nextNodeId: 'wisdom-ending' },
        { id: 'name-treasure', text: '"I want to share your treasure with the world."', nextNodeId: 'deal-ending' },
      ],
    },

    'speak-name-peaceful': {
      id: 'speak-name-peaceful',
      title: 'Recognition',
      content: `You speak the ancient name. Verathrax's eyes widen with surprise, then soften with something like hope.

"You learned my true name... and yet you approach in peace? Perhaps there is hope for your kind after all."

The dragon closes its book and gestures for you to sit. "Come. We have much to discuss, you and I."`,
      choices: [
        { id: 'discuss-future', text: 'Discuss the future with the dragon', nextNodeId: 'peace-ending' },
      ],
    },

    'mercy-plea': {
      id: 'mercy-plea',
      title: 'A Plea for Mercy',
      content: `You drop everything and fall to your knees. "Please! I was a fool! Spare me!"

The dragon regards you for a long moment. "Greed brought you here, but fear makes you honest. Very well. Take one item—one—and leave. Never return."

You grab a single golden chalice and flee into the night.`,
      choices: [
        { id: 'escape-mercy', text: 'Flee with your prize', nextNodeId: 'escape-ending' },
      ],
    },

    // === ENDINGS ===
    'peace-ending': {
      id: 'peace-ending',
      title: 'The Dawn of Peace',
      content: `Together, you and Verathrax forge a plan. The dragon will reveal itself to the village—not as a monster, but as a guardian, a keeper of ancient knowledge.

It takes time, but slowly, trust grows. The dragon teaches the villagers the old ways, healing arts and forgotten lore. In return, they bring books and companionship.

You become the first Dragon Ambassador, traveling between human and dragon territories, building bridges of understanding.

Years later, when young adventurers ask about your greatest treasure, you smile.

"The greatest treasure," you say, "was learning that some things are more valuable than gold."

**THE END - PEACE ACHIEVED**`,
      choices: [],
      isEnding: true,
      endingType: 'victory',
    },

    'wisdom-ending': {
      id: 'wisdom-ending',
      title: 'The Student',
      content: `You stay with Verathrax, learning the secrets of ages past. The dragon teaches you magic, history, philosophy—knowledge that no gold could buy.

When you finally return to the village, you are changed. You carry no treasure, but your eyes hold the light of ancient wisdom.

You become a sage yourself, passing on the dragon's teachings. And sometimes, when students doubt, you take them up the mountain to meet your oldest friend.

**THE END - WISDOM GAINED**`,
      choices: [],
      isEnding: true,
      endingType: 'victory',
    },

    'deal-ending': {
      id: 'deal-ending',
      title: 'The Partnership',
      content: `Verathrax considers your proposal. "A partnership? You would share my treasure with the world, in exchange for..."

"Protection," you say. "You guard the wealth. I distribute it fairly—to those in need, to build schools and hospitals. You'll never be hunted again, because the people will love their dragon."

The dragon laughs—a warm, rumbling sound. "Clever. Very clever. I accept."

And so begins the legend of the Dragon's Bank, which brings prosperity to the land for generations to come.

**THE END - PROSPERITY FOR ALL**`,
      choices: [],
      isEnding: true,
      endingType: 'victory',
    },

    'victory-hollow': {
      id: 'victory-hollow',
      title: 'A Hollow Victory',
      content: `You return to the village laden with gold, hailed as a hero. The wealth makes you powerful, respected, feared.

But at night, you dream of amber eyes and rumbling laughter. Of conversations that might have been. Of wisdom you'll never learn.

You have everything you wanted. Why does it feel like nothing?

**THE END - VICTORY, BUT AT WHAT COST?**`,
      choices: [],
      isEnding: true,
      endingType: 'neutral',
    },

    'defeat-ending': {
      id: 'defeat-ending',
      title: 'The Long Walk Home',
      content: `You limp back to Millbrook, wounded in body and spirit. The villagers tend your wounds, but the questions in their eyes are harder to bear than any flame.

You tell them the truth: the dragon is too powerful to defeat. And perhaps... perhaps it doesn't need to be defeated at all.

Some call you a coward. Others see something else in your eyes—wisdom, hard-won and bitter.

You never return to the mountain. But sometimes, on quiet nights, you wonder about the dragon, reading its books alone in the dark.

**THE END - SURVIVAL, BARELY**`,
      choices: [],
      isEnding: true,
      endingType: 'defeat',
    },

    'escape-ending': {
      id: 'escape-ending',
      title: 'The Escape',
      content: `You return to the village with your single golden chalice. It's worth a small fortune—enough to live comfortably for years.

But you never speak of the mountain. When young adventurers ask for directions to the dragon's lair, you shake your head.

"There's nothing there for you," you say. "Trust me."

Some listen. Most don't. You try not to count the ones who never return.

**THE END - THE SURVIVOR**`,
      choices: [],
      isEnding: true,
      endingType: 'neutral',
    },

    'leave-empty': {
      id: 'leave-empty',
      title: 'The Retreat',
      content: `You turn and walk away. The dragon watches you go, surprise flickering in its ancient eyes.

"Wait," it calls. You stop but don't turn around.

"No one has ever left before. Take something—anything. Please."

You consider for a moment, then shake your head. "Keep your treasure. I came for gold, but I think I was looking for something else all along."

You walk down the mountain, lighter than when you arrived. Behind you, you could swear you hear the dragon laugh—not mockingly, but with something like respect.

**THE END - THE ONE WHO WALKED AWAY**`,
      choices: [],
      isEnding: true,
      endingType: 'neutral',
    },
  },
};
