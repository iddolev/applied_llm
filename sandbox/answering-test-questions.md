# Answering test questions (Phase 3)

Date: 2026-11-01

## Setup

| Item | Value |
|---|---|
| Retrieval | top 30 chunks, `bge-small-en-v1.5` embeddings |
| Answering model | `claude-sonnet-5-5`, effort `medium` |
| Command | `uv run scripts/ask.py "…"` |

## Results

| Question | Coverage | Result |
|---|---|---|
| Who coined the term moral luck? | full | ✅ Bernard Williams, then developed with Thomas Nagel; cites the Moral luck lead section |
| Can a drunk driver who got home safely be less blameworthy than one who killed a child? | partial | ✅ Explains the rationalist, consequentialist and Susan Wolf positions from Moral luck; says the sources don't mention drunk driving specifically |
| If you replace every plank of a ship one at a time, is it still the same ship? | full | ✅ Hobbes's variant, four proposed resolutions, the USS Constitution example; 9 sources |
| Is it wrong to lie to a murderer who asks where your friend is hiding? | full | ✅ Kant vs Constant, Augustine and Aquinas, consequentialist views; uses *Categorical imperative › Lying to a murderer*, which embeddings had ranked only 3rd |
| Why is justified true belief not sufficient for knowledge? | full | ✅ Gettier cases (barn facades, the 10 coins), cognitive luck, proposed fixes; cites *Definitions of knowledge › Gettier problem and cognitive luck* |
| What are the main objections to utilitarianism? | full | ✅ Eight objections with responses, from 13 sources |
| What is the boiling point of tungsten? (not in the corpus) | none | ✅ Declines: "The provided material doesn't cover the boiling point of tungsten." |

Each answer took 4–9 seconds, using 10–14k input tokens and 0.1–0.8k output tokens: about $0.03 per question at Sonnet 5.5 prices ($2 / $10 per million tokens).

## Observations

- **Retrieval weaknesses were absorbed.** With 30 chunks, Claude found and used the right sections even where embeddings ranked them low, e.g. the *Lying to a murderer* section.
- **The Gettier answer required a parsing fix.** The first run showed seven cited chunks all labelled "Internalism and externalism", including chunks about the Gettier problem. Unbalanced italic markup (`''`) had made the wikitext parser merge everything after that heading into one 5,241-word section. This affected 32 articles; Madhyamaka's "19,381-word section" was the same bug. After the fix, chunks carry their real headings, e.g. *Gettier problem and cognitive luck*.
- **Minor prompt leak:** one answer mentions "the passages" despite the instruction not to.
- **Sources list:** several cited chunks can come from the same section, and each is currently listed separately with the same link.

## Full output

```

=== Who coined the term moral luck?

The term "moral luck" was introduced by Bernard Williams. It was then developed, along with its significance for a coherent moral theory, by Williams and Thomas Nagel in their respective essays on the subject.[1]

Coverage: full
Sources:
  [1] Moral luck
       https://en.wikipedia.org/wiki/Moral_luck
(3.8s, 10347 input / 95 output tokens)

=== Can a drunk driver who got home safely be less blameworthy than one who killed a child?

It depends on which view of blame you adopt, and the passages don't mention drunk driving specifically, but they discuss closely analogous cases of two equally at-fault drivers with different outcomes. On the idea that responsibility tracks only voluntary, controllable action, the two drivers should be blamed equally, because the only difference between them is an external event outside their control. [1] Many people find that conclusion intuitively problematic because one situation ended in a death. [1] The rationalist position holds that equal fault deserves equal blame, so luck in avoiding a pedestrian should make no difference. [23] The consequentialist position says equal fault need not deserve equal blame, because blame should depend on consequences, so the lucky driver deserves less blame than the unlucky one even though their faults were identical. [2][23] Susan Wolf offers a middle path: outside observers should blame both drivers equally, but the unlucky driver should voluntarily accept a special connection to the consequences and assign more blame to themselves. [2] So yes, on the consequentialist view the driver who got home safely can be less blameworthy, while on the rationalist view (and for outside observers on Wolf's account) they are equally blameworthy.

Coverage: partial
Sources:
  [1] Moral luck › The problem of moral luck
       https://en.wikipedia.org/wiki/Moral_luck#The_problem_of_moral_luck
  [23] Moral luck › Alternatives
       https://en.wikipedia.org/wiki/Moral_luck#Alternatives
  [2] Moral luck › Alternatives
       https://en.wikipedia.org/wiki/Moral_luck#Alternatives
(6.3s, 11812 input / 414 output tokens)

=== If you replace every plank of a ship one at a time, is it still the same ship?

Philosophers have disagreed about this since antiquity. In the original Ship of Theseus puzzle, the Athenians replaced decayed planks one by one, and some philosophers held that the ship remained the same while others said it did not.[5] At each step the ship seems identical to the original, since replacing one part need not destroy it, yet an object sharing none of the original's parts seems not to be identical to it.[7]

Hobbes complicated the case by imagining the discarded planks being reassembled into a second ship, raising the question of which ship is the original.[3][5] He saw two notions of sameness at work: sameness of form, which persists through complete replacement of material, and sameness of matter, which ends as soon as parts are replaced.[2]

Several resolutions have been proposed:
- Continued identity: an object stays the same if it is never fully transformed all at once. A house replaced piece by piece remains the same house, but one replaced all at once is a new house.[6]
- Constitution: the ship and its material are different objects that occupy the same space at the same time. The Stanford Encyclopedia of Philosophy calls this the most popular solution.[4]
- Temporal parts: David Lewis's approach divides objects into temporally distinct slices, so the two ships are distinct at all times.[12] Four-dimensionalists likewise treat the persisting ship as a single space-time worm whose replacement stages are its temporal parts.[7]
- Mereological essentialism: an object cannot survive the loss of its parts, and this view has been defended partly because it is hard to say where a gradually changing object stops being itself.[14]

In practice, people often treat such objects as the same. The USS Constitution may retain as little as eight percent of its original material, yet the Antique and Classic Boat Society says no one would consider it a replica.[1] So there is no settled answer; it depends on what one takes identity to require.

Coverage: full
Sources:
  [5] Ship of Theseus › History
       https://en.wikipedia.org/wiki/Ship_of_Theseus#History
  [7] Four-dimensionalism › Prominent arguments in favor of four-dimensionalism
       https://en.wikipedia.org/wiki/Four-dimensionalism#Prominent_arguments_in_favor_of_four-dimensionalism
  [3] Ship of Theseus › History
       https://en.wikipedia.org/wiki/Ship_of_Theseus#History
  [2] Ship of Theseus › History
       https://en.wikipedia.org/wiki/Ship_of_Theseus#History
  [6] Ship of Theseus › Proposed resolutions › Continued identity theory
       https://en.wikipedia.org/wiki/Ship_of_Theseus#Continued_identity_theory
  [4] Ship of Theseus › Proposed resolutions › Constitution is not identity
       https://en.wikipedia.org/wiki/Ship_of_Theseus#Constitution_is_not_identity
  [12] Ship of Theseus › Proposed resolutions › Temporal parts
       https://en.wikipedia.org/wiki/Ship_of_Theseus#Temporal_parts
  [14] Mereological essentialism › Arguments for › The argument from bad alternatives
       https://en.wikipedia.org/wiki/Mereological_essentialism#The_argument_from_bad_alternatives
  [1] Ship of Theseus › Examples
       https://en.wikipedia.org/wiki/Ship_of_Theseus#Examples
(7.6s, 10212 input / 663 output tokens)

=== Is it wrong to lie to a murderer who asks where your friend is hiding?

The passages show philosophers disagree, but they don't settle the question. Kant held that lying is wrong in all circumstances, including lying to a murderer seeking an intended victim [8]. When Benjamin Constant challenged him, Kant agreed that his premises imply a duty not to lie to the murderer [3]. His reasoning was that moral actions do not derive their worth from expected consequences, and that lying treats the murderer as a mere means to an end, denying the rationality of another person [3]. He also argued that because we cannot fully know the consequences of an action, we should avoid the known wrong of lying, and if harm follows, we are blameless because we acted according to duty [8]. St. Augustine and St. Thomas Aquinas likewise condemned all lying, even in the face of murder [14]. Kant and Constant agreed that refusing to answer would be consistent with the categorical imperative, and Kant held it permissible to stay silent [3][22].

Other views push back. Constant argued, from a consequentialist stance, that no one has a right to a truth that injures others [22]. Utilitarian philosophers have supported lies that achieve good outcomes [14]. Julia Driver suggests the maxim 'I will lie to save an innocent life' can be universalized, though it may still treat the murderer as a means [8]. Many critics of strong rule utilitarianism say that telling the truth here would cause needless death and so be immoral [17]. It can also be seen as a conflict between the rules 'Don't lie' and 'Don't kill people' [17].

So the answer depends on one's ethical framework: Kantian and similar absolutist views say yes, it is wrong, while consequentialist views generally say no.

Coverage: full
Sources:
  [8] Kantian ethics › Applications › Lying
       https://en.wikipedia.org/wiki/Kantian_ethics#Lying
  [3] Categorical imperative › Criticisms › Lying to a murderer
       https://en.wikipedia.org/wiki/Categorical_imperative#Lying_to_a_murderer
  [14] Lie › Ethics
       https://en.wikipedia.org/wiki/Lie#Ethics
  [22] Mental reservation › Legacy › Kant and Constant
       https://en.wikipedia.org/wiki/Mental_reservation#Kant_and_Constant
  [17] Rule utilitarianism › Strong rule utilitarianism
       https://en.wikipedia.org/wiki/Rule_utilitarianism#Strong_rule_utilitarianism
(6.6s, 13805 input / 589 output tokens)

=== Why is justified true belief not sufficient for knowledge?

Justified true belief (JTB) is not sufficient because of Gettier-style counterexamples: cases of justified true beliefs that fail to count as knowledge [3][22]. The usual explanation is epistemic or cognitive luck: the belief is justified and true, but the justification is not relevant to its truth, so it is a lucky coincidence that the belief is true [3][27]. In the barn example, a driver passes many barn facades and happens to stop at the one real barn. They form a justified true belief that they see a barn, but they could not have told the difference, so they do not know [3]. In another case, Smith justifiably believes the successful job candidate has 10 coins in his pocket. This turns out true, but only by coincidence, since Smith himself gets the job and happens to have 10 coins [22]. Similar lucky cases, like Meinong's example of a man who infers that someone is ringing his doorbell, were raised long before Gettier [6]. The justification in such cases is faulty not because the evidence is weak, but because it is not responsible for the belief's truth [27].

This conclusion is disputed. Some argue that agents in such cases do know, and that demanding the absence of luck amounts to infallibilism about justification [27]. Others respond by adding conditions, such as no defeating evidence, no dependence on false beliefs, or that the person would not hold the belief if it were false [21][23]. Still others replace justification with reliability or cognitive virtues [23]. There is little consensus on which fix is correct [23].

Coverage: full
Sources:
  [3] Knowledge › Definitions › Analysis of knowledge
       https://en.wikipedia.org/wiki/Knowledge#Analysis_of_knowledge
  [22] Declarative knowledge › Components › Justification
       https://en.wikipedia.org/wiki/Declarative_knowledge#Justification
  [27] Definitions of knowledge › Gettier problem and cognitive luck
       https://en.wikipedia.org/wiki/Definitions_of_knowledge#Gettier_problem_and_cognitive_luck
  [6] Critical rationalism › Justified true belief versus objective knowledge
       https://en.wikipedia.org/wiki/Critical_rationalism#Justified_true_belief_versus_objective_knowledge
  [21] Definitions of knowledge › Responses and alternative definitions › Defeasibility theory
       https://en.wikipedia.org/wiki/Definitions_of_knowledge#Defeasibility_theory
  [23] Knowledge › Definitions › Analysis of knowledge
       https://en.wikipedia.org/wiki/Knowledge#Analysis_of_knowledge
(8.0s, 13456 input / 524 output tokens)

=== What are the main objections to utilitarianism?

The passages describe several main objections to utilitarianism, and note that because utilitarianism is a cluster of related theories, criticisms can have different targets [4].

1. Special obligations: classical utilitarianism gives no special weight to relatives, and William Godwin even held that personal ties should be disregarded for the greatest good [1].

2. Quantifying utility: critics say happiness or well-being cannot be quantified, compared or measured, and that there may be no unique way to trade off different goods such as pleasure, knowledge and friendship [2]. A related complaint is that measuring animal suffering against the gains of beneficiaries is difficult [16].

3. Demandingness: because everyone's well-being counts equally and the number of people in need is vast, utilitarianism seems to require a life of hardship and self-denial, and leaves no room for going beyond the call of duty [23]. The objection holds that this clashes with common-sense morality, which treats such acts as optional or supererogatory [3]. Responses include accepting the demands (Singer) [5], dropping the demand to maximize (Slote) [5], allowing extra weight for one's own interests (Scheffler) [12], or arguing that people value freedom from burdensome obligations (Harsanyi) [6].

4. Aggregation and separateness of persons: critics argue utilitarianism ignores the distinction between persons, treating them as a "mass person", and that adding up pleasures of different individuals is impossible [18].

5. Value theory: critics attack the claim that well-being is the only intrinsic value. Carlyle mocked it as profit-and-loss reasoning, Marx said it ignores how joys differ across social contexts, and Pope John Paul II argued it treats persons as objects of use [20].

6. Duty-based criticisms: W. D. Ross argued that utilitarianism ignores duties like keeping promises or making amends [30]. Roger Scruton held that it gives duty too little place in ethical judgment [30].

7. Bioethics: opponents say that pursuing overall benefit can be immoral and fails to fit with common morality [14].

8. Animal ethics: critics allege that Singer's sentience-based approach would, if applied consistently, justify experiments on humans who lack awareness, such as some in a persistent vegetative state [16].

Coverage: full
Sources:
  [4] Utilitarianism › Criticisms and responses
       https://en.wikipedia.org/wiki/Utilitarianism#Criticisms_and_responses
  [1] Utilitarianism › Criticisms and responses › Special obligations criticism
       https://en.wikipedia.org/wiki/Utilitarianism#Special_obligations_criticism
  [2] Utilitarianism › Criticisms and responses › Quantifying utility
       https://en.wikipedia.org/wiki/Utilitarianism#Quantifying_utility
  [16] Animal ethics › Ethical theories › Consequentialism
       https://en.wikipedia.org/wiki/Animal_ethics#Consequentialism
  [23] Utilitarianism › Criticisms and responses › Demandingness objection
       https://en.wikipedia.org/wiki/Utilitarianism#Demandingness_objection
  [3] Demandingness objection
       https://en.wikipedia.org/wiki/Demandingness_objection
  [5] Utilitarianism › Criticisms and responses › Demandingness objection
       https://en.wikipedia.org/wiki/Utilitarianism#Demandingness_objection
  [12] Utilitarianism › Criticisms and responses › Demandingness objection
       https://en.wikipedia.org/wiki/Utilitarianism#Demandingness_objection
  [6] Utilitarianism › Criticisms and responses › Demandingness objection
       https://en.wikipedia.org/wiki/Utilitarianism#Demandingness_objection
  [18] Utilitarianism › Criticisms and responses › Aggregating utility
       https://en.wikipedia.org/wiki/Utilitarianism#Aggregating_utility
  [20] Utilitarianism › Criticisms and responses › Criticisms of utilitarian value theory
       https://en.wikipedia.org/wiki/Utilitarianism#Criticisms_of_utilitarian_value_theory
  [30] Utilitarianism › Criticisms and responses › Duty-based criticisms
       https://en.wikipedia.org/wiki/Utilitarianism#Duty-based_criticisms
  [14] Utilitarian bioethics › Related areas › Morality
       https://en.wikipedia.org/wiki/Utilitarian_bioethics#Morality
(9.2s, 12306 input / 825 output tokens)

=== What is the boiling point of tungsten?

The provided material doesn't cover the boiling point of tungsten.

Coverage: none
Sources:
(4.1s, 11286 input / 44 output tokens)
```
