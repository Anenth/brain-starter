# Cases

Each file here is **one mistake a real run made**. It is kept so the mistake can't
come back without someone seeing it.

## Run them

```bash
python3 tests/run_cases.py                  # every case. Needs claude, logged in
python3 tests/run_cases.py standup          # only files with "standup" in the name
python3 tests/run_cases.py --show           # print the prompts, call nothing
python3 tests/run_cases.py --rev <commit>~1 standup  # the rule as it was before the fix
python3 tests/test_cases.py                 # offline. Files parse, rules still found
```

Run them after changing a skill or routine that a case names in `rules:`.

## Add one

When a mistake gets fixed, copy an existing case and fill it in:

- `rules:` the file with the rule the run should have followed. `anchor:` the first
  line of that rule, so only that part goes in the prompt.
- **Task.** What the run was doing, and what to output. Keep it to one small output.
- **Input.** What the run saw. Only the part that matters. No phone numbers, no
  comp, health or legal detail.
- **Must not match / Must match.** Regexes. Code first. Test them on the real bad
  output and on a good one.
- **Judge.** One yes/no question. Pass and Fail in plain words. The real bad output
  goes in as the Fail example. `tests/test_cases.py` checks the code checks catch it.

Then run it with `--rev <fix commit>~1`. It should fail there. If it passes, the
case has no teeth. Make the input closer to what the run really saw.
