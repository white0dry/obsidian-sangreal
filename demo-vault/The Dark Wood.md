---
aliases:
  - Inferno Notes
type: Commentary
author: Dante Alighieri
date: 2026-10-22
pages: 128
archived: true
tags:
  - sample
  - dante
  - inferno
---

This is the sample note for the **Sangreal** theme. It puts the common note styles on one page: **bold**, *italic*, ***bold italic***, ~~strikethrough~~, ==highlight==, `inline code`, an internal link to [[The Gate of Hell]], an external link to [obsidian.md](https://obsidian.md), a #sample tag, and a footnote.[^1]

# I. The Dark Wood

Dante sets the poem in the spring of 1300, when he was thirty-five: half of the seventy years the Psalms allow a life. He wakes in a wood with no memory of how he entered it, tries to climb a sunlit hill, and is driven back by three beasts. Help comes from below, in the shape of a dead poet, and the only way out turns out to lead down (see [[Inferno, Canto III]]).

## The Gate of Hell

> All hope abandon, ye who enter in!
> — *Inferno*, Canto III, line 9

The inscription is the most quoted line of the poem, and the least read in context. It closes nine lines in which the gate itself speaks: where it leads, who built it, and what it asks of those who pass. Dante does not understand it, and says so.

> Midway upon the journey of our life.

### The Three Beasts

- The leopard, light and swift, with a spotted skin
  - Most often read as lust, or as fraud
    - Some commentators tie it to the politics of Florence
      - Dante was exiled from Florence in 1302 and never returned
  - It blocks the way up the hill so often that he turns back again and again
- The lion, head uplifted and ravenous, so that the air seems afraid of him
- The she-wolf, the worst of the three: Virgil says she lets no one pass her way

The order of the descent:

1. Pass through [[The Gate of Hell]] and cross the Acheron in Charon's boat
2. Wake on the far bank in [[Limbo]], then go down to [[The Second Circle]]
3. Keep going, since the only way out of the wood is through

This week:

- [ ] `[ ]` To do: copy out the inscription of *[[Inferno, Canto III]]* by hand
- [/] `[/]` In progress: annotate Canto IV, the noble castle
- [x] `[x]` Done: read Canto I aloud
- [-] `[-]` Cancelled: map all nine circles before finishing Canto V
- [>] `[>]` Deferred: the *Purgatorio*, until the *Inferno* is done
- [<] `[<]` Scheduled: reread Canto V on Sunday
- [!] `[!]` Important: check line 9 of Canto III against the Italian
- [?] `[?]` Question: what kind of beast is the *lonza*, really?
- [*] `[*]` Star: there is no greater sorrow than to be mindful of the happy time
- ["] `["]` Quote: thou art my master, and my author thou
- [i] `[i]` Info: Longfellow's translation was published in 1867
- [b] `[b]` Bookmark: Canto V, line 121
- [l] `[l]` Location: Ravenna, where Dante died in 1321
- [I] `[I]` Idea: draw the descent as a spiral

#### Who's Who in Cantos I–V

| Figure   | Role                          | Canto |
| :------- | :---------------------------- | ----: |
| Virgil   | Guide, poet of the *Aeneid*   |     1 |
| Beatrice | Sends Virgil to Dante's aid   |     2 |
| Charon   | Ferryman of the Acheron       |     3 |
| Minos    | Judge at the second circle    |     5 |

##### Note: Terza Rima

Dante's tercets interlock: the middle line of each sets the rhyme of the next, so the verse can only move forward. Qian Daosun, the first to put these cantos into Chinese, copied the scheme with the old rhyme groups of classical Chinese.

###### Sixth-level heading

The smallest heading, for the briefest of marginal notes.

## The Second Circle

The second circle is smaller than the first and holds more pain. The lustful are blown about by a storm that never stops, the way starlings are carried by the winter wind. Out of the crowd come two souls who are never apart, and Francesca tells their story while Paolo weeps. My notes from the last few days are in [[2026-10-20]] and [[2026-10-21]].

> [!note]
> Every canto ends on a single line that closes the rhyme of the last tercet.

> [!abstract]
> Five cantos, 707 lines: a dark wood, a refused journey, a gate, the noble castle of Limbo.

> [!info]
> Longfellow keeps Dante's line count exactly, but gives up the rhyme.

> [!todo]
> Compare Qian Daosun's 1924 version of Canto III with Longfellow's.

> [!important]
> Virgil can lead Dante only as far as reason reaches. 

> [!tip]
> Read Canto III aloud: the threefold "Through me" of the inscription is meant to be heard.

> [!success]
> Cantos I–V read and annotated.

> [!question]
> Why does Dante faint at the end of Canto III, and again at the end of Canto V?

> [!warning]
> Minos coils his tail once for each circle a soul must go down.

> [!failure]
> Paolo and Francesca never finish the book they were reading.

> [!danger]
> The infernal hurricane that never rests.

> [!bug]
> The poem's clock runs ahead: events after 1300 appear in it as prophecies.

> [!example]
> Terza rima in Canto I: *vita · oscura · smarrita*, then *dura · forte · paura*. That is aba bcb.

> [!quote]
> Love, that on gentle heart doth swiftly seize.

> [!tip]- A foldable callout (click to expand)
> A folded callout shows only its title until opened.

---

# II. The Translations

## Copies and Code

```python
def terza_rima(tercets: int) -> str:
    # aba bcb cdc ... and one closing line
    a = "abcdefghijklmnopqrstuvwxyz"
    return " ".join(a[i] + a[i + 1] + a[i] for i in range(tercets)) + " " + a[tercets]
```

```css
.sangreal {
  color: #a3161f;
  background: #fbf7ef;
}
```

## Formulae

One opening canto and three canticles of thirty-three make the hundred: $1 + 3 \times 33 = 100$.

A canto of $t$ tercets has $L$ lines (Canto I: $t = 45$, $L = 136$):

$$
L = 3t + 1
$$

## The Descent

```mermaid
graph LR
  A[Dark Wood] --> B[Gate of Hell]
  B --> C[Acheron]
  C --> D[Limbo]
  D --> E[Second Circle]
```

## The City He Lost

Dante never saw Florence again after 1302. The city Corot painted from the Boboli Gardens is not the one he left: the cathedral dome and Giotto's bell tower on its skyline both rose after his death.

![[corot-florence.jpg]]

*Jean-Baptiste-Camille Corot, View of Florence from the Boboli Gardens, c. 1835, Musée du Louvre. Public domain.*

## Embedding Another Note

![[The Gate of Hell#The Inscription]]

[^1]: This is a footnote. English quotations follow Longfellow's translation (1867); footnotes are gathered at the end of the note.
