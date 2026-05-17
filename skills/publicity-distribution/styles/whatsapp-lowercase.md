# Style: whatsapp lowercase

the way you'd text a friend who happens to work in your field. all lowercase, short lines, no ceremony.

## why it works

it signals that you did not run this through a content calendar. on x, in discord, and among indie builders and researchers, lowercase reads as native and as low-effort in the good sense: someone typed this because they had a thought, not because tuesday is posting day.

it also makes ai tells physically hard to write. "leverage our robust, seamless infrastructure" does not survive being typed in lowercase. it starts looking ridiculous, which is the point.

## rules

- everything lowercase. including the first word, including "i", including proper nouns where it doesn't cause confusion. keep capitalisation for things where lowercase would be wrong or confusing: `PostgreSQL`, `GPT-5`, someone's name when you're crediting them.
- short lines. break where you'd pause if you were saying it.
- minimal punctuation. periods at the end of a thought are optional. no semicolons. obviously no em dashes.
- parentheses are fine and natural (they're how people add an aside when texting)
- contractions always. "it's", "doesn't", "we'd"
- start mid-thought. "ok so the timeout was the whole problem" is a fine opener.
- trailing thoughts are fine. "anyway. it works now"
- one emoji maximum, and only if it's doing something. usually zero.
- no hashtags
- fragments are fine. not every line needs a verb.

## what it is not

this is not sloppiness. the thinking underneath should be as rigorous as the professional style, and the specifics should be just as concrete. lowercase with no substance is worse than sentence case with substance, because the casualness makes the emptiness more obvious.

it's also not baby talk. no "smol", no "uwu", no forced quirkiness. it's just a person typing normally.

## where it fits

| Platform | Fit |
|---|---|
| X / Twitter | native, often the default |
| Discord | native |
| Instagram captions | works well |
| LinkedIn | works if the account has an established personality. risky for a company page. |
| Medium / Substack body | no, use it in the intro at most |
| YouTube description | title in sentence case, description can be lowercase |

## example

```
the eval runner used to lose everything when a task crashed

you got a stack trace and whatever had scrolled past in tmux. so finding out
what the model actually did on turn 4 meant re-running the whole thing, about
three hours

now every turn goes to disk as it happens. tool calls, args, results, reasoning
traces, token counts

the annoying discovery: most of what we'd been calling model failures were our
own harness timing out at 30s on steps that genuinely needed 90

runs ~40 episodes in parallel on one box. viewer is a terminal ui not a web
dashboard, which some people will hate

still can't diff runs across providers in any way that isn't lying about one
of them. if anyone's solved that i'd like to know

repo: <link>
```

## converting from professional to lowercase

it is not a find-and-replace on capital letters. the sentence structures differ.

professional: "We identified that the primary bottleneck was an undocumented timeout in the harness configuration."

lowercase: "turned out the harness had a 30s timeout nobody knew about"

shorter, more direct, and the second one tells you the actual number.
