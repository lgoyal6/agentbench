# demo.tape — AgentBench CLI demo for a GitHub profile README
#
# All setup lives in demo-setup.sh, which is *sourced* inside a Hide block so
# no long command is ever typed on screen (prevents line-wrap garble) and the
# screen is cleared before Show (prevents any setup leaking into a frame).
#
# The two visible commands render real numbers from benchmarks/v0.1.0/ — no
# live API call, so the GIF is fast and deterministic.
#
# Run from the repo root:  vhs demo.tape

Output demo.gif

Set Shell "bash"
Set FontSize 18
Set Width 1400
Set Height 410
Set Theme "Dracula"
Set TypingSpeed 40ms
Set Padding 20

Hide
Type "source demo-setup.sh && clear" Enter
Sleep 3s
Show

Type "agentbench report --input benchmarks/v0.1.0/claude-haiku-4-5.json" Enter
Sleep 3s
Type "agentbench leaderboard show --suite math_reasoning" Enter
Sleep 3500ms
