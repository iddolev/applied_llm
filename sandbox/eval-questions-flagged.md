# Evaluation questions: flagged for review

150 questions were kept. This file lists questions that need a human decision.

## Included, but flagged in manual review (5)

Notes from data/eval/review_notes.json. Keep, reword or drop?

### lookup-004 (lookup)

**Q:** In the illustration of epistemic commitment involving Susan and Joe, what does Susan claim killer whales really are, and what does Joe say they actually are?

**Reference answer:** Susan claims killer whales are whales, first because the name contains 'whale' and then because they look like other whales. Joe says they are actually dolphins, despite the name.

**Seed passages:** Epistemic commitment › Example 2
**Word overlap with passages:** 0.5
- **Review note:** Refers to the article's own example ('the illustration involving Susan and Joe'), which a real user wouldn't know about. Reword to ask about the concept, or drop.

### scenario-030 (scenario)

**Q:** My friend Dana has started four businesses in six years. Each time, just as one begins to stabilize, she drops it for some exciting new idea that hasn't been tested yet. She tends to leave relationships when a fresh romantic prospect appears, and she runs herself ragged chasing change. She makes decisions on strong hunches rather than careful analysis. How would Carl Jung's theory of personality types classify someone like her?

**Reference answer:** Jung would likely call Dana an extroverted intuitive type. For such a person, intuition, which Jung saw as an irrational function and as perception via the unconscious, dominates over rational judgment. This type is drawn outward to new, promising but unproven possibilities. They often abandon ventures, and even lovers, before these bear fruit, and they neglect their own welfare in the pursuit of change. Jung thought such people were often entrepreneurs or speculators.

**Seed passages:** Intuition; Intuition › Psychology › Freud; Intuition › Psychology › Jung
**Word overlap with passages:** 0.2
- **Review note:** Names the theory it is about ('Carl Jung's theory of personality types'), so it is closer to a lookup than a scenario.

### multihop-017 (multihop)

**Q:** India's Supreme Court in 2017 recognized a certain protection as a human right while a national biometric ID scheme was being challenged. Roughly how many national constitutions mention that same protection, and which Indian intelligence agency has been named among those conducting mass global surveillance that threatens it?

**Reference answer:** In 2017, during the challenge to the Aadhaar biometric ID project, India's Supreme Court declared privacy a human right. The right to privacy is mentioned in over 185 national constitutions. India's R&AW is named alongside the NSA, FBI, CIA and GCHQ as an agency that has engaged in mass global surveillance.

**Seed passages:** Privacy › Legal right to privacy › By country › India; Right to privacy
**Word overlap with passages:** 0.67
- **Review note:** Contrived: it chains two unrelated facts (how many constitutions mention privacy; which Indian agency does surveillance) rather than one fact that leads to the other.

### negation-005 (negation)

**Q:** In the field known as the history of knowledge, whose work do the publications of Philip Sarasin, a co-founder of the Zurich research center, reflect?

**Reference answer:** Philip Sarasin's publications, as a co-founder of the history-of-knowledge institution at the University of Zurich, mirror the work of Michel Foucault.

**Seed passages:** History of knowledge › Concepts
**Word overlap with passages:** 0.69
- **Review note:** Doesn't test negation or relations; it is a plain lookup ('whose work do Sarasin's publications reflect?').

### unanswerable-014 (unanswerable)

**Q:** In which of Plato's dialogues does Socrates first draw a contrast between how things appear on the surface and their true underlying nature, and roughly when was that dialogue written?

**Reference answer:** A correct answer would need to name a specific Platonic dialogue where the appearance/reality (surface vs. depth) contrast is developed, such as the Republic with its allegory of the cave, and give its approximate composition date (around 375 BC). The corpus says only that the superficiality-versus-depth distinction goes back to Plato's time. It does not identify any dialogue or date.

**Seed passages:** Superficiality
- **Review note:** Has no clear true answer ('which dialogue first draws the appearance/reality contrast' is debatable), so even a good system can't be graded against it.

## Included, but sharing at least 80% of their vocabulary with their passages (5)

These may be too easy for retrieval. Keep, reword or drop?

### lookup-006 (lookup)

**Q:** Why did Denis Hilton call his model of everyday causal explanation the "conversational" model?

**Reference answer:** Because he argued that explanation, unlike prediction, is a social activity that needs an audience — someone to whom the event or action is being explained. He held that causal explanations follow Grice's manner and quantity maxims, with the explainer tailoring the explanation to the audience's needs.

**Seed passages:** Folk psychology › Key folk concepts › Explanation › Conversational Model
**Word overlap with passages:** 0.88

### lookup-018 (lookup)

**Q:** In which work did Anselm of Canterbury set out his ontological argument for God, and in which chapters?

**Reference answer:** Anselm presented his ontological argument in chapters 2 and 3 of his Proslogion, which was a meditative work rather than an attempt to prove God's existence.

**Seed passages:** Ontological argument › Development › Anselm
**Word overlap with passages:** 1.0

### lookup-032 (lookup)

**Q:** According to William Lane Craig, in what senses does the Bible usually use the words "true" and "truth"?

**Reference answer:** Craig observes that the Bible typically uses these words in non-philosophical senses, to indicate qualities such as fidelity, moral rectitude, and reality. Only sometimes does it use them in the philosophical sense of veracity.

**Seed passages:** Religious views on truth › Abrahamic religions › Christianity
**Word overlap with passages:** 0.8

### multihop-021 (multihop)

**Q:** Formal systems for reasoning about 'if...then' statements are used in several fields, one of which is a computational discipline. What are the traditional research goals of that computational field?

**Reference answer:** Conditional logics are applied in artificial intelligence, among other fields. AI's traditional research goals are learning, reasoning, knowledge representation, planning, natural language processing and perception, along with support for robotics.

**Seed passages:** Conditional logic; Artificial intelligence
**Word overlap with passages:** 0.85

### broad-007 (broad)

**Q:** Was Samkhya philosophy theistic or atheistic, and what arguments did it give against a creator God?

**Reference answer:** 

- Scholars distinguish theistic (seśvara, 'with lord') and non-theistic (nirīśvara, 'without lord') streams of Samkhya; the Svetasvatara Upanishad exemplifies the former and the Samkhyakarika the latter.
- Some scholars hold that an older theistic Samkhya appears in the Upanishads and Puranas, and that it later shifted toward atheistic realism and pluralism under Jaina and Buddhist influence. Later commentators such as Vijnanabhiksu tried to revive its theism.
- Many scholars see acceptance of a personal god as a key difference between Yoga and Samkhya. Others, such as Phukan, argue Samkhya is as theistic as Yoga, and many think Ishvara entered Samkhya only through its association with Yoga and other schools.
- Classical Samkhya accepted higher or perfected selves and an emergent Isvara absorbed into prakṛti, but disputed an eternal creator Isvara. Texts such as the Sāṁkhyapravacana Sūtra declare God's existence unproved.
- Metaphysically, an unchanging God cannot be the source of an ever-changing world.
- If karma operates, God is unnecessary as a moral governor, since karma itself delivers consequences.
- Even without karma, God cannot be the enforcer of consequences. An altruistic God would not create a world full of suffering. An egoistic God would need desire, which conflicts with his eternal freedom, and desire belongs to prakṛti anyway. A God with unfulfilled desires would suffer and be no better than a higher self.
- No means of knowledge establishes God: he is not perceived, no inference proves him, and the Vedas name prakṛti as the world's origin. Hence the cosmological, ontological and teleological arguments fail.

**Seed passages:** Samkhya › Views on God; Samkhya › Views on God; Samkhya › Views on God; Samkhya › Views on God › Arguments against Ishvara's existence; Samkhya › Views on God › Arguments against Ishvara's existence
**Word overlap with passages:** 0.86

## Rejected by validation (37)

Excluded from the set. Any that look fine can be rescued.

### lookup-007 (lookup)

**Q:** Who proved the stronger uncertainty relations that give non-trivial bounds on the sum of variances of two incompatible observables, even when the Robertson–Schrödinger relation becomes trivial?

**Reference answer:** Lorenzo Maccone and Arun K. Pati proved these stronger uncertainty relations. They bound the sum of the variances of two non-commuting observables, which stays informative even when the system is in an eigenstate of one observable, where the Robertson–Schrödinger relation becomes trivial.

**Seed passages:** Uncertainty principle › Mathematical formalism › The Maccone–Pati uncertainty relations
**Word overlap with passages:** 0.88
- copies wording: The question lifts distinctive phrasing almost verbatim from the passage, e.g. 'stronger uncertainty relations', 'give non-trivial bounds on the sum of variances', 'two incompatible observables'. This turns it into a string-matching exercise.

### lookup-029 (lookup)

**Q:** According to Nietzsche, what political movement is the direct descendant of Christianity and the political expression of slave morality?

**Reference answer:** The democratic movement. Nietzsche regards it as Christianity's heir and as slave morality in political form, because of its preoccupation with freedom and equality.

**Seed passages:** Master–slave morality › Slave morality
**Word overlap with passages:** 0.6
- copies wording: The question closely echoes the passage's wording: 'heir to Christianity' is paraphrased only as 'direct descendant', and 'political manifestation of slave morality' is nearly verbatim.

### lookup-033 (lookup)

**Q:** In the debate over Patanjali's stages of samadhi, how many types of samāpatti did Vācaspati Miśra propose, and what do the joy-related ones take as their object of support?

**Reference answer:** Vācaspati Miśra proposed eight types of samāpatti. The two joy-related ones, sānanda- and nirānanda-samāpatti, take the sense organs as their objects of support.

**Seed passages:** Samadhi › Hinduism › Patanjali's Yoga Sūtras › Samprajñata samādhi › Ānanda and asmitā
**Word overlap with passages:** 0.46
- doesn't fit its type: The question combines two separate facts: the number of samāpatti types and the object of support for the joy-related ones. A lookup question should ask for a single specific fact.

### lookup-038 (lookup)

**Q:** In William Rowe's well-known evidential version of the problem of evil, what concession does he make about suffering, and why does he still think God's existence is unlikely?

**Reference answer:** Rowe grants that some cases of intense suffering do bring about greater goods. He denies, however, that this holds for every case, and argues that an all-powerful, all-knowing, wholly good being would probably have prevented at least some instances of suffering.

**Seed passages:** Theism › Arguments › Against
**Word overlap with passages:** 0.53
- doesn't fit its type: The question is compound: it asks for both Rowe's concession and his reasoning. A lookup question should ask for one specific fact.

### lookup-046 (lookup)

**Q:** Which principle does Martha Nussbaum favor over disgust-based morality as the proper basis for limiting individual liberty in law and policy?

**Reference answer:** She sides with John Stuart Mill's harm principle, which she sees as supporting legal ideas such as consent, the age of majority, privacy and equal rights for citizens.

**Seed passages:** Wisdom of repugnance › Reactions and criticism
**Word overlap with passages:** 0.92
- copies wording: The question lifts phrases almost verbatim from the passage: "disgust-based morality", "law and policy", and "proper basis for limiting individual liberty" (passage: "liberties").

### scenario-001 (scenario)

**Q:** At a book club, one member argues that a novel can be brilliantly written and still count as great art even if it celebrates cruelty, so its ugly values are irrelevant to how good it is. Another member insists you can't judge any artwork apart from the moral codes of the people who make and read it, and adds that stories like this could even push readers toward copying what they see. What longstanding philosophical disagreement are they having, and what positions are they taking?

**Reference answer:** This is the debate over the relationship between art and morality. The first member holds that art is independent of morality: being morally reprehensible doesn't strip a work of its art status or its aesthetic value. The second member sees art and morality as linked, either through a supervenience-like relation in which the human side of art only makes sense alongside human moral codes, or because art can influence behaviour for good or ill. Critics of violent films, for example, have blamed them for copycat acts.

**Seed passages:** Art and morality › History and ideas; Art and morality › History and ideas; Art and morality › History and ideas
**Word overlap with passages:** 0.15
- doesn't fit its type: The scenario largely restates the passage's positions in near-passage language instead of describing a concrete situation. The second member's line ('can't judge any artwork apart from the moral codes of the people who make and read it') paraphrases the supervenience claim and reuses 'moral codes'. The first member's line echoes 'does not deny an artwork its art status'. Putting both tenets in the characters' mouths, combined with 'art' and 'moral', practically names the art-and-morality debate. That makes the question trivial and breaks the rule against listing the doctrine's tenets.
- copies wording: The scenario largely restates the passage's positions in near-passage language instead of describing a concrete situation. The second member's line ('can't judge any artwork apart from the moral codes of the people who make and read it') paraphrases the supervenience claim and reuses 'moral codes'. The first member's line echoes 'does not deny an artwork its art status'. Putting both tenets in the characters' mouths, combined with 'art' and 'moral', practically names the art-and-morality debate. That makes the question trivial and breaks the rule against listing the doctrine's tenets.

### scenario-006 (scenario)

**Q:** A group of people is designing the rules for a new society, but none of them knows what career, religion, or personal goals they will end up with. To decide what the rules should distribute fairly, they agree to focus on things like basic rights and freedoms, income and wealth, and conditions that support people's self-respect, since anyone would want these whatever their eventual plans. What idea is guiding their choice of what to distribute, and why does it fit their situation?

**Reference answer:** They are relying on Rawls's notion of primary goods: things any rational person wants whatever their particular plans, or, in the later formulation, what citizens need as free people and members of society. Social primary goods include rights, liberties, income and wealth, and the social bases of self-respect. Because everyone values them regardless of their unknown future goals, they give a shared basis on which all parties, choosing from behind their ignorance (Rawls's original position), can unanimously agree on principles of justice.

**Seed passages:** Primary goods
**Word overlap with passages:** 0.19
- doesn't fit its type: The scenario lists the passage's catalogue of social primary goods (rights and liberties, 'income and wealth', bases of self-respect) and states the defining property ('anyone would want these whatever their eventual plans'). This spells out the doctrine's tenets and largely gives away the answer, contrary to the scenario-type rules. It also reuses the passage's wording.
- copies wording: The scenario lists the passage's catalogue of social primary goods (rights and liberties, 'income and wealth', bases of self-respect) and states the defining property ('anyone would want these whatever their eventual plans'). This spells out the doctrine's tenets and largely gives away the answer, contrary to the scenario-type rules. It also reuses the passage's wording.

### scenario-008 (scenario)

**Q:** On a camping trip, three friends argue about God. One says God is simply nature itself, nothing over and above the trees and stars. Another insists God exists entirely outside the universe, untouched by physical laws and beyond what any human mind can grasp. The third says God is present in every leaf yet also exceeds the whole cosmos. Is the third friend contradicting herself, and how would each friend's position usually be classified?

**Reference answer:** The third friend is not contradicting herself. The second friend describes God's transcendence: existence completely independent of, and beyond, the material universe, possibly also beyond human knowledge. The first friend's view, that God is indistinguishable from the world, is pantheism. Transcendence is defined as the opposite of immanence (God fully present in the physical world), but the two are not necessarily mutually exclusive. The third friend's view, that God both pervades and surpasses the universe, is panentheism.

**Seed passages:** Transcendence (religion); Transcendence (religion) › In Abrahamic religions › Judaism; Transcendence (religion) › In Abrahamic religions › Judaism
**Word overlap with passages:** 0.27
- ambiguous: Asking how 'each friend's position' is classified invites several valid labels the passage doesn't settle. The second friend's view could be called deism or classical theism, not just 'transcendence', which is an attribute rather than a named position. The first friend's view could arguably be immanentism rather than pantheism. The question also bundles three classifications plus a yes/no, diluting the focus on a single concept. 'Beyond what any human mind can grasp' closely echoes the passage's wording.

### scenario-011 (scenario)

**Q:** Two friends are debating whether an ancient stargazer could have been wrong in believing that the bright 'evening star' and the 'morning star' were different objects. One friend says that since both names actually refer to the planet Venus, it could never have turned out otherwise, so there is no possible scenario in which they are distinct. The other says that saying 'the evening star is not the morning star' breaks no rule of reasoning and involves no contradiction, so it's still possible in some sense. Who is right, and in what sense?

**Reference answer:** Both are right about different kinds of possibility. Many philosophers following Kripke hold that the identity is metaphysically necessary, because both names pick out the same object in every possible world where they refer. But it is still logically possible for the identity to be false, because denying it violates no rule of logic, such as consistency. This illustrates the view that logical possibility is a broader notion than metaphysical possibility.

**Seed passages:** Logical possibility; Logical possibility
**Word overlap with passages:** 0.11
- doesn't fit its type: The friends' statements spell out the doctrine's tenets: one gives the rigid-reference argument for necessity, the other gives the consistency criterion for logical possibility. This leaves little for the answerer to supply beyond the labels. The scenario also just re-skins the passage's own Hesperus/Phosphorus example. The opening framing is muddled: the stargazer clearly was wrong, which is not what is actually debated.

### scenario-016 (scenario)

**Q:** My friend glanced out the window and said, "The train is already at the platform, but I don't believe it is." Everyone laughed as if she'd said something ridiculous. Yet if she had said, "The train was at the platform, but I didn't believe it was," or "The train is at the platform, but you don't believe it is," nobody would have batted an eye. Her original remark wasn't actually self-contradictory, since the train could be there without her believing it. So why does it sound so absurd?

**Reference answer:** This is Moore's paradox, first noticed by G. E. Moore. A sentence of the form "P, but I don't believe that P," said in the first person and present tense, can be true and is logically consistent. It is perfectly possible for the train to be there while she doesn't believe it, yet asserting it seems absurd. Past-tense versions and versions about other people sound fine, and philosophers still have no generally accepted explanation of why only the first-person present-tense assertion is absurd.

**Seed passages:** Moore's paradox; Moore's paradox › The problem; Moore's paradox › The problem
**Word overlap with passages:** 0.28
- doesn't fit its type: The scenario restates the doctrine's diagnostic tenets almost point for point from passage 3. It includes the past-tense counterpart being fine, the second-person counterpart being fine, and the remark being logically consistent and not self-contradictory. That goes beyond describing what happened and effectively spells out Moore's own presentation of the paradox, which the type instructions forbid.

### scenario-032 (scenario)

**Q:** A woman notices her young nephew is unusually gentle with stray animals. Her grandmother says this is because the boy's soul lived before in another body, perhaps even as an animal, and that his deeds in that earlier life shaped the life he has now. She adds that he will keep being born again until his soul is purified enough to be freed from the cycle. What belief is the grandmother expressing, and in which traditions is it found?

**Reference answer:** She is describing reincarnation (also called rebirth or transmigration): the idea that some aspect of a being begins a new life in a different body or form after each death. In the Indian doctrine of saṃsāra and karma, souls pass through human and animal forms, and the nature of each new existence is set by actions in previous lives. The cycle continues until the soul is purified and reaches liberation. The belief is held in Hinduism, Buddhism, Jainism and Sikhism, and it also appears among ancient Greeks such as Pythagoras and Plato and in movements like theosophy.

**Seed passages:** Afterlife; Afterlife › Different metaphysical models; Afterlife › Different metaphysical models › Reincarnation
**Word overlap with passages:** 0.28
- doesn't fit its type: The grandmother's speech recites the doctrine's tenets almost point by point: past life in another body, animal forms, deeds shaping the next life, repeated rebirth until the soul is purified and freed from the cycle. This closely paraphrases passage 3 and makes the concept trivially identifiable, which goes against the scenario rule of not listing tenets. The add-on 'in which traditions' part is also open-ended.

### scenario-038 (scenario)

**Q:** A woman visiting an ashram in India notices that some residents spend their days serving in the kitchen, others sing devotional hymns to Krishna, and a third group sits with a teacher, repeatedly asking themselves "Who am I, really?" and then meditating on whether their true self is anything other than their body and thoughts. Within Hindu tradition, what spiritual approach is that third group following, and what is it supposed to accomplish?

**Reference answer:** They are following jñāna yoga, the "path of knowledge" or self-realization. It is one of the three classical paths to liberation (moksha) in the Bhagavad Gita, alongside karma yoga (the kitchen workers' path of action) and bhakti yoga (the singers' path of devotion). Usually guided by a guru, practitioners use inquiry, study, reflection and meditation to reach liberating insight into the Self (Atman) and its relationship to Brahman. In the Gita this involves discerning pure consciousness (purusha) from matter and material desires (prakriti), which the calming effect of meditation makes possible. This knowledge brings liberation either in this life or after death.

**Seed passages:** Jñāna yoga; Jñāna yoga › Etymology; Jñāna yoga › Definition
**Word overlap with passages:** 0.14
- copies wording: The scenario borrows the passage's signature example question 'Who am I?' almost verbatim. It also hints at the Atman inquiry ('true self... other than body and thoughts'), which makes identifying the concept close to string-matching rather than applying it.

### multihop-004 (multihop)

**Q:** Chisholm described human agents as unmoved prime movers of their own actions. Which broader family of positions on free will does his view fall under, and how does that family's other main branch differ from it about determinism?

**Reference answer:** Chisholm's agent-causal view belongs to metaphysical libertarianism, a form of incompatibilism, the view that free will cannot coexist with determinism. Libertarians hold that determinism is false, so free will is at least possible. The other branch, hard determinism or hard incompatibilism, holds that determinism is true, so free will is not possible.

**Seed passages:** Libertarianism (metaphysics) › Agent-causal theories; Free will
**Word overlap with passages:** 0.44
- copies wording: The question lifts Chisholm's distinctive 'prime mover unmoved' phrasing from passage 1, only lightly rearranged. 'Broader family' is slightly loose: it could be read as libertarianism rather than incompatibilism, though 'other main branch' points to incompatibilism. Passage 1's text does not explicitly call agent causation libertarian; that link comes only from the section title.

### multihop-008 (multihop)

**Q:** There's a term for a hypothesis that fits with current science but hasn't yet been adequately checked by the standard empirical procedure of science. What does that procedure require of a hypothesis for it to be meaningfully tested at all?

**Reference answer:** Such a hypothesis is called protoscience: one not yet adequately tested by the scientific method but consistent with existing science, or able to reasonably explain any inconsistency. The scientific method requires that hypotheses be falsifiable. It must be possible to identify an outcome of an experiment or observation that would conflict with predictions deduced from the hypothesis; otherwise it cannot be meaningfully tested.

**Seed passages:** Pseudoscience › Boundaries with science › Classification; Scientific method
**Word overlap with passages:** 0.5
- doesn't fit its type: The multi-hop is superficial. The question asks only what the scientific method requires (falsifiability), which passage 2 answers on its own. 'Standard empirical procedure of science' identifies the scientific method without any help from passage 1, and the protoscience term is never actually asked for. The question also reuses the passage-2 phrase 'meaningfully tested'.
- copies wording: The multi-hop is superficial. The question asks only what the scientific method requires (falsifiability), which passage 2 answers on its own. 'Standard empirical procedure of science' identifies the scientific method without any help from passage 1, and the protoscience term is never actually asked for. The question also reuses the passage-2 phrase 'meaningfully tested'.

### multihop-010 (multihop)

**Q:** Informal fallacies often trace back to vague or double-meaning words in the kind of language people ordinarily speak. How is that kind of language defined, and what sorts of languages are excluded from it?

**Reference answer:** Ambiguous and vague expressions in natural language often cause the faulty reasoning behind informal fallacies, such as fallacies of ambiguity like the 'feathers are light' argument. A natural language is any spoken or signed language that arises organically in a human community without conscious planning, is passed down across generations, and changes gradually over time. Excluded are artificial or constructed languages (e.g., those invented for fiction), formal logical and programming languages, non-human communication systems like whale songs or bee dances, and certain human communication systems with no native speakers.

**Seed passages:** Logical reasoning › Fallacies; Natural language
**Word overlap with passages:** 0.5
- doesn't fit its type: Not a real multi-hop question. The question itself states the passage-1 fact (fallacies stem from ambiguous or vague words in ordinary language) and practically names passage 2's topic ('the kind of language people ordinarily speak' is ordinary/natural language). So everything it actually asks can be answered from passage 2 alone. The reference answer also adds passage-1 details (the 'feathers are light' example) that the question never asks for.

### multihop-012 (multihop)

**Q:** The philosopher who accused Hobbes of simply imagining already-socialized people living outside society also wrote a book whose title gave its name to a whole theory of political legitimacy. What is that theory, and how does it say a legitimate state comes about?

**Reference answer:** The critic of Hobbes was Jean-Jacques Rousseau. His 1762 book The Social Contract gave its name to social contract theory. That theory holds that a legitimate state arises when citizens agree to give up some of their freedoms and submit to an authority, either a ruler or the majority's decisions. In return, their remaining rights are protected or social order is maintained.

**Seed passages:** State of nature › Noted philosophers › Jean-Jacques Rousseau; Social contract
**Word overlap with passages:** 0.61
- copies wording: The question closely echoes passage 1's distinctive phrasing ('simply imagining ... living outside ... society', 'socialized people'). This makes the hop to Rousseau a near lexical match rather than a real inference. It is otherwise a sound multi-hop question.

### multihop-014 (multihop)

**Q:** In first-order logic, when exactly is a substitution idempotent, i.e. applying it twice gives the same result as applying it once? Given the logical form of that criterion, what can you conclude about a substitution such as {x ↦ x+y}, and about one in which no replaced variable shows up in any replacement term?

**Reference answer:** A substitution {x1 ↦ t1, …, xk ↦ tk} (with each xi ≠ ti) is idempotent if and only if none of the variables xi occurs in any of the terms tj. Because the criterion is a biconditional, both sides must be true together or false together, so the condition is both necessary and sufficient. Thus {x ↦ x+y}, where x appears in its own replacement term, cannot be idempotent. A substitution in which no replaced variable appears in any replacement term is guaranteed to be idempotent.

**Seed passages:** Substitution (logic) › First-order logic; If and only if
**Word overlap with passages:** 0.35
- doesn't fit its type: The multi-hop link is weak. Passage 1 alone gives the full criterion and explicitly states that {x ↦ x+y} is non-idempotent. The 'no replaced variable appears' case is simply the criterion itself, so passage 2's account of biconditionals is not actually needed. The phrase 'given the logical form of that criterion' asks for passage 2 nominally, but no fact from it is required to answer the question.

### multihop-025 (multihop)

**Q:** The thinkers who argued that all forms of popular culture serve to keep the masses obedient to market interests belonged to a school of thought tied to a particular research institute. When and at which university was that institute founded?

**Reference answer:** The idea that popular culture forms a single industry keeping the masses obedient to market interests came from Adorno and Horkheimer of the Frankfurt School. That school is associated with the Institute for Social Research, founded on February 3, 1923, at the University of Frankfurt am Main (now Goethe University Frankfurt).

**Seed passages:** Culture industry › The Frankfurt School; Frankfurt School
**Word overlap with passages:** 0.6
- copies wording: The question closely paraphrases passage 1's distinctive wording ('all ... forms of popular culture', 'obedience of the masses to market interests'), which makes the first hop easy to match lexically.

### multihop-032 (multihop)

**Q:** The Italian Marxist who pictured capitalist domination as a half-human, half-beast creature to explain why Western Europe escaped a communist revolution gave his name to a broader concept of ruling-class dominance. What term does that concept's name come from, and what is the term called when the same kind of social control is imposed by another society?

**Reference answer:** Gramsci's concept of cultural hegemony, which he pictured as a centaur combining coercion with consent, takes its name from the Ancient Greek word hegemonia, meaning the leadership or rule of a hegemon. When this kind of social control is exercised by another society, it is called cultural imperialism.

**Seed passages:** Power (political science) › Theories › Cultural hegemony; Cultural hegemony
**Word overlap with passages:** 0.55
- ambiguous: The question wrongly says Gramsci 'gave his name to' the concept. Cultural hegemony is not named after him; per passage 1 he elaborated it. This false premise could mislead answerers toward something like 'Gramscianism'. The question also bundles two sub-questions, and both answers come from passage 2. Passage 1 serves only to identify the concept.

### broad-017 (broad)

**Q:** How do contextualist approaches in philosophy and psychology differ from one another, and why does the purpose of an analysis matter so much to them?

**Reference answer:** Contextualism relies on having a clear analytic goal, because both its pragmatic test of truth and its focus on acts in context only make sense relative to a goal. Varieties of contextualism are distinguished by their goals and fall into descriptive and functional types, which differ in aims, emphasis and the kind of knowledge they produce.

- Contextualism's truth criterion of 'successful working' is meaningless without an explicit goal, since success can only be measured against an objective.
- Without a goal there is no basis for limiting analysis of an act's infinite historical and environmental context, so one could never know when an analysis is complete or adequate.
- Varieties of contextualism are distinguished by their analytic goals and divide into descriptive contextualism and functional contextualism.
- Descriptive contextualism seeks a rich, personal, aesthetic understanding of whole events, emphasizing the root metaphor of the act-in-context, much like history.
- Descriptive contextualist knowledge is personal, ephemeral, specific and tied to a particular time and place; examples include social constructionism, dramaturgy, hermeneutics and narrative approaches.
- Functional contextualism aims to predict and influence events using empirically based concepts and rules, emphasizing the practical truth criterion, much like science or engineering.
- Functional contextualists reject rules or theories that do not serve practical goals, and their knowledge is general, abstract and applicable across times and places.

**Seed passages:** Functional contextualism › Varieties of contextualism; Functional contextualism › Varieties of contextualism › Descriptive contextualism; Functional contextualism › Varieties of contextualism › Functional contextualism
**Word overlap with passages:** 0.44
- ambiguous: The phrase 'contextualist approaches in philosophy and psychology differ from one another' can be read as asking how philosophical contextualism differs from psychological contextualism. The passages instead distinguish descriptive from functional contextualism by analytic goal, and say nothing about a philosophy-vs-psychology split. The question should explicitly ask about the varieties or kinds of contextualism.

### broad-029 (broad)

**Q:** How have different thinkers throughout history, from antiquity through the early modern period, explained what is wrong with greed or why it seems insatiable?

**Reference answer:** 

- Aristophanes satirized the idea that while people tire of other pleasures, the desire for wealth never ends: each gain only makes them want more.
- Ambrose of Milan held that the earth belongs to everyone, not just the rich, and that avarice destroys the mutual concern that creates and binds society.
- Aquinas saw greed as a sin against God, choosing temporal over eternal things, and also against one's neighbor, since one person's excess riches mean another's lack.
- Luther condemned the usurer as humanity's greatest enemy after the devil, someone who would let the world starve so as to have everything for himself while posing as pious.
- Locke argued that property beyond what one can use before it spoils is wasteful, offends against nature, and belongs to others.
- Adam Smith noted that appetite for food is limited by the stomach, but the desire for luxuries like housing, clothing and furniture seems boundless.
- In Goethe's Faust, avarice is personified and linked to living beyond one's means, and Faust laments that being rich still leaves one feeling a lack.

**Seed passages:** Greed › Views of greed › In animals; Greed › Views of greed › Ancient views › Aristophanes; Greed › Views of greed › Ancient views › St. Ambrose; Greed › Views of greed › Medieval Europe › Aquinas; Greed › Views of greed › Early modern Europe › Luther; Greed › Views of greed › Early modern Europe › Locke; Greed › Views of greed › Early modern Europe › Adam Smith; Greed › Views of greed › Modern period › Goethe
**Word overlap with passages:** 0.31
- ambiguous: The question limits its scope to 'antiquity through the early modern period', but the passages file Goethe under 'Modern period', and the reference still includes a Goethe point. This creates a scope mismatch: a correct answer could reasonably leave Goethe out. Otherwise the key points are accurate and draw on all the passages.

### negation-002 (negation)

**Q:** In modern logic, why is a contradiction not automatically a philosophical problem, and what kind of contradiction is a clear example of a harmless one?

**Reference answer:** In modern logic, a contradiction is simply the conjunction of a statement and its negation (A and not-A), a notion that is neutral about whether anything is provable or justified. It therefore includes contradictions derived on purpose in a proof by contradiction, where the point is to refute one of the assumptions. So not every contradiction is philosophically troubling.

**Seed passages:** Antinomy › Terminology
**Word overlap with passages:** 0.5
- doesn't fit its type: The question is a 'why' explanation plus example question, not a negation/relation question about who rejected, opposed, influenced or differed from whom. No role-swapping structure is present.

### negation-008 (negation)

**Q:** If philosophy is understood as a not-yet-mature science that spins off disciplines once firm knowledge becomes possible, which branches of philosophy fit that picture poorly, and what other objection does the picture face?

**Reference answer:** The picture fits moral and political philosophy poorly, since closeness to science does not apply equally to all parts of philosophy. It also struggles to account for the seriousness and importance of philosophers' achievements, including those that shaped the sciences, because calling philosophy immature implies philosophers cannot pursue their research properly.

**Seed passages:** Definitions of philosophy › Based on relation to science › As an immature science
**Word overlap with passages:** 0.4
- doesn't fit its type: The question is a compound question asking for the listed disadvantages of a view. It is not a negation/relation question about who rejected, opposed or differed from whom. No actors or roles could be swapped, and no 'not' could be dropped to flip the answer.

### negation-014 (negation)

**Q:** Why did Nietzsche reject Kant's notion of the thing in itself, and what did he blame for people believing in it?

**Reference answer:** Nietzsche, not Kant, is the critic here. He attacked the Kantian noumenon, or thing in itself, as indeterminate, self-contradictory and not worth pursuing. He traced belief in it to the misleading influence of language and our linguistic habits. He grouped it with other such fictions, like the atom in the science of his day and the notion of the subject.

**Seed passages:** Indeterminacy (philosophy) › Indeterminacy in philosophy › Nietzsche and the indeterminacy of the "thing in itself"
**Word overlap with passages:** 0.38
- doesn't fit its type: The question is a compound 'why' explanation question rather than a relation/negation question. Both roles are given outright, so swapping them or dropping a 'not' would not test the relation. The reference answer also opens with an odd, unprompted 'Nietzsche, not Kant, is the critic here.'

### negation-018 (negation)

**Q:** Whose vegetarianism was James Joyce critical of, even though scholars argue his novel Ulysses still takes up questions of animal ethics?

**Reference answer:** Joyce was critical of the vegetarianism of George A.E. Russell. Even so, the scholar Peter Adkins argues that Ulysses engages with animal ethics through its depiction of Ireland's cattle industry, animal slaughter and the cultural significance of meat.

**Seed passages:** Vegetarianism › Media › Literature
**Word overlap with passages:** 0.6
- copies wording: The question reuses passage phrasing nearly verbatim, including 'critical of the vegetarianism' and the quoted phrase 'questions of animal ethics'. It also says 'scholars argue' when the passage cites only one scholar, Peter Adkins.

### unanswerable-004 (unanswerable)

**Q:** When Kant published the second edition of the Critique of Pure Reason, what new section did he add to answer readers who accused his transcendental idealism of being no different from Berkeley's idealism?

**Reference answer:** A correct answer would say that the 1787 second edition added the "Refutation of Idealism." In it Kant argued that our awareness of our own existence as determined in time depends on the existence of persisting things outside us. He meant this to separate his position from Berkeleyan and Cartesian (problematic) idealism. This is a historical and textual detail that the material on transcendental idealism does not cover.

**Seed passages:** Transcendental idealism
- answered by retrieved passages: ["Idealism › Modern philosophy › Epistemic idealism › Kant's Transcendental idealism"]

### unanswerable-005 (unanswerable)

**Q:** In what year did the Society for American Archaeology formally adopt its Principles of Archaeological Ethics?

**Reference answer:** A correct answer would give the year the Society for American Archaeology adopted its Principles of Archaeological Ethics (1996). The corpus discusses archaeological ethics generally, mentioning UNESCO's 1970 action, the Nuremberg Code and the Declaration of Helsinki, but not when this professional society adopted its code.

**Seed passages:** Archaeological ethics
- answered by retrieved passages: ['Archaeological ethics › Laws and protections around the world › America']

### unanswerable-006 (unanswerable)

**Q:** In which year did Alexius Meinong publish his essay on the theory of objects, which argued that there are objects that do not exist?

**Reference answer:** A correct answer would need to give the publication year of Meinong's "Über Gegenstandstheorie" ("On the Theory of Objects"), which appeared in 1904. The corpus covers existence and ontology conceptually but does not provide this bibliographic detail.

**Seed passages:** Existence
- answered by retrieved passages: ['Nonexistent objects › Round square copula']

### unanswerable-007 (unanswerable)

**Q:** In what year was the book that introduced the argument model built around claims, grounds, warrants and qualifiers first published, and who wrote it?

**Reference answer:** A correct answer would identify Stephen Toulmin's The Uses of Argument, first published in 1958, as the source of this model. The corpus describes the structure of practical arguments but not who devised it or when it was published.

**Seed passages:** Practical arguments › Overview...
- answered by retrieved passages: ['Rhetoric of science › Developments and trends › Argument fields']

### unanswerable-008 (unanswerable)

**Q:** In what year did Noam Chomsky first publish the book in which he laid out his theory of generative grammar, and what was its title?

**Reference answer:** A correct answer would give the title and year of Chomsky's first major book on generative grammar: Syntactic Structures, published in 1957. This is a bibliographic fact about Chomsky, not something a concept-focused article on universal grammar would cover.

**Seed passages:** Universal grammar
- answered by retrieved passages: ['Syntax › Theoretical syntactic models › Generative syntax']

### unanswerable-009 (unanswerable)

**Q:** In which year did Charles Darwin publish The Descent of Man, the book where he discussed the evolutionary origins of the moral sense?

**Reference answer:** A correct answer would state that The Descent of Man, and Selection in Relation to Sex was published in 1871. This is a bibliographic detail about Darwin, which a corpus of concept articles is unlikely to cover.

**Seed passages:** Natural morality
- answered by retrieved passages: ['Evolutionary ethics › History']

### unanswerable-013 (unanswerable)

**Q:** In which book did Hedley Bull first put forward the idea of a 'new medievalism' in world politics, and when was it published?

**Reference answer:** A correct answer would name Hedley Bull's book 'The Anarchical Society: A Study of Order in World Politics' and give its publication year, 1977. The corpus links the concept to Bull but does not name the work or give a date.

**Seed passages:** Neo-medievalism
- answered by retrieved passages: ['Neo-medievalism › Political theory']

### unanswerable-017 (unanswerable)

**Q:** In what year did H.L.A. Hart publish The Concept of Law, his major defense of legal positivism?

**Reference answer:** A correct answer would give the publication year of H.L.A. Hart's The Concept of Law, which was 1961. This is a bibliographic fact about a specific book and author, not something covered in material on the concept of positive law.

**Seed passages:** Positive law
- answered by retrieved passages: ['Legal positivism › History › H. L. A. Hart', 'Legal realism › Criticisms']

### unanswerable-019 (unanswerable)

**Q:** In what year did Henry Sidgwick first publish The Methods of Ethics, the book in which he examined egoism alongside utilitarianism?

**Reference answer:** A correct answer would give the first publication date of Sidgwick's The Methods of Ethics, which was 1874. This bibliographic detail is not something an article on the concept of ethical egoism would be expected to cover.

**Seed passages:** Ethical egoism
- answered by retrieved passages: ['Ethical egoism › History']

### unanswerable-021 (unanswerable)

**Q:** Who first introduced the idea of psychical distance in aesthetics, and in what year was that essay published?

**Reference answer:** A correct answer would name Edward Bullough, who introduced 'psychical distance' as an aesthetic principle in his essay published in the British Journal of Psychology in 1912. It would need that originating author and publication date, which the material here does not provide.

**Seed passages:** Psychic distance
- answered by retrieved passages: ['Psychic distance › Aesthetics']

### unanswerable-022 (unanswerable)

**Q:** Which ancient author first described the fallacy of missing the point (ignoratio elenchi), and in what work did he discuss it?

**Reference answer:** A correct answer would need to identify Aristotle as the first to describe ignoratio elenchi and name the work, his Sophistical Refutations (part of the Organon), where he treats it as a fallacy arising from a misunderstanding of what a refutation is. The corpus passage only defines the fallacy and does not cover its historical origin.

**Seed passages:** Irrelevant conclusion
- answered by retrieved passages: ['Irrelevant conclusion › Overview']

### unanswerable-026 (unanswerable)

**Q:** Who first coined the term "ecological fallacy," and in what year was it introduced?

**Reference answer:** A correct answer would name the sociologist credited with introducing the term (Hanan C. Selvin, 1958, building on W. S. Robinson's 1950 paper on ecological correlations) and give the year. The corpus describes the fallacy but does not cover its coinage.

**Seed passages:** Ecological fallacy
- answered by retrieved passages: ["Ecological fallacy › Examples › Robinson's paradox"]
