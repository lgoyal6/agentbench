# API reference

Generated with [mkdocstrings](https://mkdocstrings.github.io/). When building
the docs site with `mkdocs build`, the directives below expand into full
auto-generated references with cross-links.

## Agent

::: agentbench.agent.AgentProtocol
::: agentbench.agent.AgentResult
::: agentbench.agent.AgentWrapper
::: agentbench.agent.NodeUsage

## Runner

::: agentbench.runner.EvalRunner
::: agentbench.runner.EvalReport
::: agentbench.runner.RunConfig
::: agentbench.runner.TrackerProtocol
::: agentbench.runner.TaskOutcome

## Metrics

::: agentbench.metrics.accuracy.Scorer
::: agentbench.metrics.accuracy.ExactMatchScorer
::: agentbench.metrics.accuracy.SemanticSimilarityScorer
::: agentbench.metrics.accuracy.LLMJudgeScorer
::: agentbench.metrics.cost.CostTracker
::: agentbench.metrics.latency.LatencyTracker
::: agentbench.metrics.composite.cost_adjusted_accuracy
::: agentbench.metrics.composite.efficiency_score

## Suites

::: agentbench.suites.base.EvalTask
::: agentbench.suites.base.EvalSuite
::: agentbench.suites.get_suite
::: agentbench.suites.list_suites
::: agentbench.suites.register_suite

## HPO

::: agentbench.hpo.runner.HPORunner
::: agentbench.hpo.runner.HPOConfig
::: agentbench.hpo.reporter.HPOResult
::: agentbench.hpo.search_space.default_search_space

## Leaderboard

::: agentbench.leaderboard.schema.LeaderboardEntry
::: agentbench.leaderboard.schema.ScoreBreakdown
::: agentbench.leaderboard.local.LocalLeaderboard
::: agentbench.leaderboard.supabase.SupabaseLeaderboard

## Integrations

::: agentbench.integrations.litellm.completion_with_capture
::: agentbench.integrations.litellm.usage_capture
::: agentbench.integrations.weave.WeaveTracker
::: agentbench.integrations.mlflow.MLflowTracker
::: agentbench.integrations.huggingface.load_hf_suite
