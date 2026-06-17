"""10 summarization tasks with reference summaries.

Tasks are scored by semantic similarity to the reference (ROUGE-style behavior
is approximated by sentence-transformers cosine similarity, which is more
forgiving of paraphrase than n-gram overlap).
"""

from __future__ import annotations

from agentbench.suites.base import EvalSuite, EvalTask

_TASKS_RAW: list[tuple[str, str, str, str]] = [
    (
        "sum-01",
        "The James Webb Space Telescope, launched in December 2021, is the largest infrared "
        "observatory ever placed in orbit. Operating from the second Lagrange point about 1.5 "
        "million kilometers from Earth, it observes extremely distant galaxies, exoplanet "
        "atmospheres, and star-forming regions that are too faint or too obscured by dust for "
        "previous telescopes.",
        "The James Webb Space Telescope, launched in 2021, is a powerful infrared observatory studying distant galaxies, exoplanets, and star formation from a point 1.5 million kilometers from Earth.",
        "easy",
    ),
    (
        "sum-02",
        "Photosynthesis is the process by which plants, algae, and some bacteria convert "
        "light energy into chemical energy stored in glucose. The reaction takes carbon "
        "dioxide and water as inputs and produces glucose and oxygen as outputs. It is the "
        "foundation of nearly every food chain on Earth.",
        "Photosynthesis is the process plants and algae use to convert light energy into glucose using carbon dioxide and water, releasing oxygen and forming the base of food chains.",
        "easy",
    ),
    (
        "sum-03",
        "Quantum entanglement is a phenomenon in which two or more particles become linked "
        "such that the quantum state of each particle cannot be described independently of "
        "the others, even when separated by large distances. Measurements on one particle "
        "instantaneously correlate with measurements on the other, which Einstein famously "
        "called 'spooky action at a distance'.",
        "Quantum entanglement links particles so their states remain correlated across any distance, producing instantaneous measurement correlations that Einstein called 'spooky action at a distance'.",
        "medium",
    ),
    (
        "sum-04",
        "Plate tectonics is the theory that Earth's outer shell is divided into several large "
        "plates that glide over the mantle. Their movements cause earthquakes, volcanic "
        "activity, mountain-building, and the formation of oceanic trenches. The theory "
        "unified previously separate observations in geology under one framework starting in "
        "the 1960s.",
        "Plate tectonics describes how Earth's crust is broken into moving plates whose interactions cause earthquakes, volcanoes, and mountains, unifying geology since the 1960s.",
        "medium",
    ),
    (
        "sum-05",
        "The Industrial Revolution, beginning in late 18th-century Britain, marked a transition "
        "from agrarian economies to ones dominated by industry and machine manufacturing. "
        "Steam power, the factory system, and innovations in iron and textile production "
        "transformed labor, urbanization, and trade across Europe and North America.",
        "The Industrial Revolution began in late 1700s Britain and shifted economies from agriculture to industry through steam power and factories, reshaping labor, cities, and trade.",
        "medium",
    ),
    (
        "sum-06",
        "CRISPR-Cas9 is a gene-editing technology that uses an RNA guide to direct the Cas9 "
        "enzyme to a specific DNA sequence, where Cas9 cuts the DNA. Cells then repair the "
        "cut, often introducing a desired edit. The system was adapted from a bacterial "
        "immune defense and has become a standard tool in modern molecular biology.",
        "CRISPR-Cas9 edits genes by using a guide RNA to direct the Cas9 enzyme to cut specific DNA, allowing edits during repair. Originally a bacterial immune system, it is now standard in molecular biology.",
        "medium",
    ),
    (
        "sum-07",
        "Climate change refers to long-term shifts in temperatures and weather patterns. Since "
        "the mid-20th century, human activities, primarily the burning of fossil fuels, have "
        "been the dominant driver of warming. Consequences include rising sea levels, more "
        "frequent extreme weather, and disruption of ecosystems.",
        "Climate change is the long-term shift in weather driven mostly by human fossil fuel use since the mid-1900s, causing sea level rise, extreme weather, and ecosystem disruption.",
        "easy",
    ),
    (
        "sum-08",
        "The transformer architecture, introduced by Vaswani et al. in 2017, replaced "
        "recurrent neural networks for many sequence tasks. Its core innovation is "
        "self-attention, which lets every position in a sequence attend to every other "
        "position in parallel, enabling much larger models and forming the basis of modern "
        "language models like GPT and BERT.",
        "The 2017 transformer architecture introduced self-attention, replacing recurrent networks, enabling parallel processing of sequences, and underlying modern language models such as GPT and BERT.",
        "hard",
    ),
    (
        "sum-09",
        "The mitochondrion is an organelle found in most eukaryotic cells, responsible for "
        "producing ATP through oxidative phosphorylation. Mitochondria have their own "
        "circular DNA and likely originated as free-living bacteria that were engulfed by "
        "an ancestral eukaryotic cell, an event called the endosymbiotic origin.",
        "Mitochondria are eukaryotic organelles that produce ATP, contain their own DNA, and likely originated from bacteria engulfed by an ancestral cell in an endosymbiotic event.",
        "medium",
    ),
    (
        "sum-10",
        "The internet emerged from ARPANET, a US Department of Defense project in the late "
        "1960s, and grew into a global network through the adoption of TCP/IP in 1983 and "
        "the invention of the World Wide Web by Tim Berners-Lee in 1989. It is now the "
        "primary medium for global communication and commerce.",
        "The internet evolved from ARPANET in the 1960s, adopted TCP/IP in 1983, and gained the World Wide Web in 1989, becoming the primary medium for global communication and commerce.",
        "hard",
    ),
]


summarization_suite = EvalSuite(
    name="summarization",
    version="0.1.0",
    description=(
        "10 short-text summarization tasks with reference summaries, scored "
        "by semantic similarity (cosine of sentence-transformers embeddings)."
    ),
    tasks=[
        EvalTask(
            id=tid,
            input={"source": src, "task": "Summarize the following text in one sentence."},
            expected_output=ref,
            difficulty=diff,  # type: ignore[arg-type]
            scorer_type="semantic",
            metadata={"category": "summarization", "max_words": 40},
        )
        for tid, src, ref, diff in _TASKS_RAW
    ],
)
