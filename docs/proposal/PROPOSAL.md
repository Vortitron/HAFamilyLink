# Kerb: a floor and a path

An open, certified standard for guiding children online, offered as a compliance route beside a minimum age, not against it.

Synthesis draft 0.3, 21 October 2026. Written for a minister, a regulator or a senior official who is about to legislate a minimum age for social media or screens. This paper is deliberately theoretical. It contains no code and no demo. It describes what should exist, why, and how to get there. Diagrams are specified in DIAGRAMS.md and imagined screens in VISUALS.md. A technical draft of the data model exists separately and is not needed to judge the argument. Material for funders and investors is kept out of this paper and lives in FUNDING-LANDSCAPE.md.

## Executive summary

Governments are legislating minimum ages for social media because a ban is the only instrument on the desk. Australia's early evidence, measured three months after commencement, shows it leaks: over 81 per cent of 10 to 15 year olds still used a restricted platform, and half of those who kept accounts were never asked their age. A ban also makes every adult prove their age. France's constitutional court struck down the French law in August 2026, mainly as a disproportionate limit on freedom of expression, and also because it forced every user to prove their age with no legal conditions or limits. About 70,000 government ID photos, by Discord's own count, leaked from a vendor handling age-verification appeals.

Kerb adds a second instrument beside the first. Keep the statutory minimum age as the floor. Add a certified, open, cross-platform standard through which a parent-managed account carries a household's own graduated plan, so a child moves above the floor as competence is shown, and a child with no engaged parent receives the statutory default automatically. Platforms honour the plan, read back what they actually did, and receive only the effects of the plan under an identifier unique to that platform. They never receive a name, date of birth, identity document, the child's competence record or the household's reasons. The child sees every rule and every reason, and sees them in the same words the parent does.

The standard rides the parent-set age signals Apple and Google already ship, is certifiable on the OpenID and IARC patterns, and sits beside ISO/IEC 27566-1. It is honest about its limits. It removes age verification only for accounts that arrive with a parent-set OS age band or a plan; it does not by itself remove the pressure to verify unmanaged accounts. Where a minimum age is set in primary legislation with no parental route, as in Australia today, the path needs an amendment, not guidance. Three asks fit a spring 2027 calendar: write "a certified graduated household plan" into secondary legislation as a future compliance route with a safe harbour for platforms that apply one, sponsor a pilot with an independent evaluation on children's outcomes, and set a twelve-month review point.

## 1. The problem as you feel it

You need a sentence, a list and a fine. Parents tell you in large numbers that their children are on screens too much and that they cannot control it. The UK consultation drew about 116,000 responses. Among the parents and carers whose answers were broken out, around nine in ten backed a minimum age of 16 ([Jurist, June 2026](https://www.jurist.org/news/2026/06/starmer-sets-spring-2027-target-for-under-16-social-media-ban/); [Medianama, June 2026](https://www.medianama.com/2026/06/223-why-uk-banning-social-media-under-16s-takeaways-public-consultation/)). Australia has acted. At least fifteen countries have enacted, passed or announced age limits ([TechCrunch, July 2026](https://techcrunch.com/2026/07/21/social-media-ban-children-countries-list/)). In September 2026 the European Commission proposed, in the KIDS Act, a minimum age of 15 for holding an independent online account ([Commission, EU age verification](https://digital-strategy.ec.europa.eu/en/policies/eu-age-verification)). Your own powers now exist in section 214A of the Online Safety Act, inserted by section 70 of the Children's Wellbeing and Schools Act 2026 ([legislation.gov.uk](https://www.legislation.gov.uk/ukpga/2026/21/section/70); [DLA Piper, April 2026](https://www.dlapiper.com/en-hu/insights/publications/2026/04/online-safety-act)).

A ban gives you the sentence, the list and the fine. This paper does not ask you to give any of them up. It asks you to add a second route that gives you the same three things, costs fewer adults their privacy, survives a court, and teaches a child something before the age the law names.

## 2. What a ban costs, on the evidence

The evidence is young. Most of it was measured three months after commencement. It is early. It already points one way.

### 2.1 Bans leak

Australia's under-16 law commenced on 10 December 2025. Platforms removed or restricted 4.7 million accounts in the first half of December, a preliminary count of accounts rather than children ([eSafety, January 2026](https://esafety.gov.au/newsroom/media-releases/platforms-restrict-access-to-47-million-under-16-accounts-across-australia)). Two findings then need reconciling, because they have different denominators. In March 2026 a pulse survey of 898 parents found that, for Instagram, Snapchat and TikTok, around seven in ten children who had an account before the law still had one; overall, parents reporting any account fell from about 50 to 31 per cent ([eSafety, March 2026](https://www.esafety.gov.au/sites/default/files/2026-03/SocialMediaMinimumAgeComplianceUpdateMarch2026.pdf)). In July 2026 eSafety published a survey of more than 4,000 children and families, measured in March 2026, which found that over 81 per cent of 10 to 15 year olds were still using at least one restricted platform, down from about 86 per cent before the law, with daily use moving from 60 to 58 per cent and account ownership from 52 to 42 per cent ([Al Jazeera, August 2026](https://www.aljazeera.com/news/2026/8/1/most-australian-teens-still-online-three-months-after-under-16-ban); [Reuters via TBS News, July 2026](https://www.tbsnews.net/tech/most-australian-teens-still-social-media-three-months-after-under-16-ban-began-study-finds)). Around half of children who kept accounts said the platform never checked their age. A separate BMJ study of 408 children in New South Wales found over 85 per cent still using covered platforms three months in, mostly through accounts they already held, with almost a fifth using a fake account, and reported "insufficient evidence to conclude that exposure to the Act had any early substantial effects" ([The National, June 2026](https://www.thenationalnews.com/future/technology/2026/06/25/age-verification-flaws-undermine-australias-social-media-ban-for-under-16s/)). Removed accounts are not removed children.

### 2.2 Bans verify adults

A minimum age can only be enforced by checking everyone. Ofcom counted over 69 million age checks on 32 UK services in the second half of 2025 ([Ofcom, July 2026](https://www.ofcom.org.uk/siteassets/resources/documents/online-safety/information-for-industry/age-assurance-report-2026/report-on-the-use-of-age-assurance.pdf)). France's Conseil constitutionnel struck down the under-15 law on 14 August 2026, mainly as a disproportionate limit on freedom of expression and communication: it reached services whose risks were not established, ignored age and maturity, and gave parents no way to lift it. It also found that forcing every user, adults included, to prove their age with no legal conditions or limits breached the right to private life ([LCP, August 2026](https://lcp.fr/actualites/reseaux-sociaux-pourquoi-le-conseil-constitutionnel-a-censure-l-interdiction-pour-les)). A US federal judge compared Texas's app-store age law to making every bookshop check every customer at the door ([9to5Mac, December 2025](https://9to5mac.com/2025/12/23/texas-judge-blocks-state-app-store-age-verification-law/)). About 850 million people worldwide have no ID at all ([EFF, October 2026](https://www.eff.org/deeplinks/2026/10/when-no-id-means-no-internet-age-verification-and-right-access-information)).

### 2.3 The data leaks

A Discord support vendor exposed government ID photos collected for age-verification appeals in Discord's UK and Australia pilot: about 70,000 by Discord's count, disputed by the attackers, who claimed far more ([The Record, October 2025](https://therecord.media/discord-government-docs-exposed-breach); [The Register, October 2025](https://www.theregister.com/2025/10/09/discord_photo_ids_leaked/)). The Tea app leaked about 13,000 verification selfies it had promised to delete ([The Record, July 2025](https://therecord.media/tea-app-data-breach-stolen-ids-leaked)). Australia's own technology trial found vendors retaining data in "over-anticipation" of regulators' needs, and found facial estimation wrongly rejecting 8.5 per cent of 16 year olds at a 16+ gate, with worse accuracy for women, darker skin and Indigenous users ([Australian Government, August 2025](https://www.infrastructure.gov.au/department/media/publications/age-assurance-technology-trial-final-report)).

### 2.4 People route around

When UK age checks went live on 25 July 2025, Proton VPN reported UK sign-ups up more than 1,400 per cent against baseline within hours of the rules taking effect ([The Register, July 2025](https://www.theregister.com/2025/07/28/uk_vpn_demand_soars/)). When Australia's adult-site checks began on 9 March 2026, Sensor Tower data showed Proton VPN moving from 174th to 19th and NordVPN from 189th to 13th on the iPhone free chart within days ([TechSpot, March 2026](https://www.techspot.com/news/111607-vpn-downloads-surge-australia-after-age-checks-hit.html); [TechRadar, March 2026](https://www.techradar.com/vpn/vpn-privacy-security/vpns-surge-in-australia-as-mandatory-age-verification-for-adult-content-begins)). Figures are vendor-reported, and should be read as direction rather than magnitude.

### 2.5 The cliff edge

A ban teaches nothing. A child is kept out until a birthday, then admitted, unprepared, into the same product. The UN Committee on the Rights of the Child asks states to respect children's "evolving capacities" as an enabling principle, to help parents favour "mutual empathy and respect, over prohibition or control", to teach digital literacy from preschool, and to limit "robust age verification" to goods and services illegal for children ([UNCRC General Comment 25, paras 19, 86, 104, 114](https://www.ohchr.org/en/documents/general-comments-and-recommendations/general-comment-no-25-2021-childrens-rights-relation)). The UK's own Children's Code protects children "within" the digital world, not from it ([ICO](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/childrens-information/childrens-code-guidance-and-resources/age-appropriate-design-a-code-of-practice-for-online-services/)). 5Rights warns that a social-media-only ban displaces children to games, AI chatbots and EdTech ([5Rights, February 2026](https://5rightsfoundation.com/access-limitations-must-be-part-of-age-appropriate-design-and-effectively-restrict-companies-from-exploiting-children/)).

Two things this paper does not argue. It does not argue that screens are harmless. The research on harm is contested, and a summary of both sides is in Appendix A. Kerb does not need screens to be harmful to be worth doing. It needs childhood to be a time of learning. And it does not argue that parents are wrong to want a ban. They want their children safe and the fighting to stop. A ban promises both. The question is whether it can deliver them alone.

## 3. The alternative: a floor and a path

### 3.1 How the two fit together

The statutory minimum age stays. It becomes the default policy that every certified platform applies to every child account that carries no household plan. A parent who never engages, never installs anything and never makes a decision gets exactly what the law would have given them. That is the answer to the hard case that drives the ban politically: the child whose parents will not engage is covered by the floor, automatically, on every certified platform.

One honest limit. Applying the floor to an account requires the platform to know the account belongs to a child. Kerb gives the platform two signals: a plan, or a parent-declared OS age band on a family account. For an account that carries neither, Kerb removes nothing of the age-assurance problem the ban has. Kerb replaces verification for parent-managed accounts, and it relies on the regulator accepting the OS-level, parent-declared band as the only signal for the rest. It does not by itself remove the pressure to verify unmanaged, adult-looking accounts. Section 7 asks for that acceptance explicitly, because without it the privacy gain is confined to managed accounts.

A parent who does engage can do more. Through a certified household controller, the parent-managed account that Apple and Google already hold carries a plan: time budgets, windows, bedtime, rules per app, and the rules that competence has earned. The platform receives the rules, never the competence. A platform that receives a plan honours it, including where it allows more than the floor, because the law of that jurisdiction permits a certified graduated household plan as a route by which a parent-managed account may graduate above the minimum. This matters. Australia's Online Safety Amendment (Social Media Minimum Age) Act 2024 is primary legislation with no parental-consent exception, and eSafety cannot create one by guidance ([Federal Register of Legislation](https://www.legislation.gov.au/C2024A00127/asmade/text)). Section 214A of the UK Act is a statutory power to set a minimum age, so the path needs the power exercised with the route written in, not a code of practice alone. The floor can be implemented everywhere now. The path requires each jurisdiction to legislate for it, and today it is impossible in Australia and would be impossible in France if its law were re-enacted unchanged. Canada's June 2026 bill already contains an opt-out for platforms that show protective policies ([TechCrunch, July 2026](https://techcrunch.com/2026/07/21/social-media-ban-children-countries-list/)). This is that idea, made specific enough to certify.

### 3.2 What "good with screens" means

The standard does not define it. Parents do. But a shared vocabulary lets a parent, a guide and a study talk about the same thing. Kerb proposes six competence milestones, each paired with one or two behaviours a parent could observe. They are descriptions, not ages. They are judgements a parent records as a milestone name and a date, not events the system logs.

1. **Stopping.** Ends a session when told; then when the timer says; then by choice. Observable: stopped at the limit without a lock on most school days this month.
2. **Choosing.** Picks apps and content for a reason they can state. Observable: can say what they made this week, not only what they watched.
3. **Meeting.** Plays and talks with known people online and knows what a stranger is. Observable: can say, when asked, what they would do if someone they do not know messaged them, and who they would tell.
4. **Noticing.** Recognises a design built to hold them and can name it: autoplay, streaks, endless feed, loot boxes. Observable: can explain why a feed keeps going.
5. **Judging.** Weighs what they see. Observable: can tell an advert from a friend.
6. **Owning.** Sets their own limits and keeps them most of the time. Observable: has chosen their own bedtime for a school week and kept it.

Milestones are parental judgements that the ledger informs. They are not scores a system assigns. A child telling a parent about a worrying message is never recorded by any Kerb component, as a milestone, a count or anything else; a disclosure that is scored stops being a disclosure. The pilot in section 8 is where the inference from ledger to readiness is tested rather than assumed.

The positive evidence for this approach is the parental mediation literature, which the harm debate tends to skip. EU Kids Online's work across Europe, and Livingstone and Helsper's studies of active against restrictive mediation, find that restriction lowers online risk but also lowers skills and opportunities, while active, enabling mediation preserves skills and protects as children grow ([Livingstone and Helsper, 2008](https://doi.org/10.1080/08838150802437396); [Livingstone et al., 2017](https://doi.org/10.1111/jcom.12277); [EU Kids Online 2020](https://www.lse.ac.uk/media-and-communications/research/research-projects/eu-kids-online)). Kerb is enabling mediation written down.

### 3.3 One child's path

Picture one child. Call her Maja.

At four, Maja has a tablet with three apps her parents chose. Everything counts. The screen shows, in pictures, how much is left.

At seven, she asks for a game. Her parents' guide tells them the game is tagged creative and offline-ok by other parents, and that it has in-app purchases. They allow it. Purchases need approval. It counts at half rate because it is building, not scrolling. Her ledger shows the rule and the reason in words she can read.

At ten, she wants voice chat with school friends. The guide shows that friends-only multiplayer is a different thing from chat with strangers, and that most families in her parents' chosen profile allow the first at ten and the second at thirteen. Her parents allow friends-only. The guide drafts the conversation about strangers, because most parents do not know how to start it.

At thirteen, she wants a social account. Her parents' guide proposes a starter policy: private by default, no endless feed, no notifications after eight, an hour a day, with every rule visible to her. The platform receives this policy through the standard, applies it, and reports back what it actually did, so her parents know it landed. Where the platform cannot honour a rule, it says so, and the household sees "unsupported", not silence.

At fourteen, the guide notices three late nights in a row. It suggests to Maja, not to her parents, that she move her own cut-off earlier. She agrees. Her parents reached the Noticing milestone with her in the spring, and from that point they stopped seeing which apps she uses. They see her totals against her budget, and whether each rule landed. The per-app detail is hers alone. Sleep is the one screen-related harm with consistent replication across studies ([Carter et al., JAMA Pediatrics 2016](https://doi.org/10.1001/jamapediatrics.2016.2341)), so bedtime is the first rule the guide protects and the last it hands over.

At fifteen, Maja's own view shows she has stopped at her limit unprompted most days for a long time, because the raw ledger is kept for a month and the guide reports the pattern to her each month. Her parents, who see only totals, hand her the evening rule. The platform receives the change the same way.

At sixteen, there is nothing to switch off. She already runs most of her own rules. The last ones end on a date she and her parents agreed, not a date a statute chose. She chooses whether to export her milestone summary or delete it. The default is deletion, and everything else is deleted either way.

### 3.4 The parent plus guide

Most parents cannot do this alone. They do not know the games, cannot read the ratings and are tired. The guide is an AI assistant that works for the family. It reads the child's ledger and the shared community knowledge. It proposes, explains and never decides. It never reads content, messages, location or browsing, and section 4.3 makes that a conformance rule on the guide and on the controller, not a hope. A guide that asks for message content is not a Kerb guide. Where the guide runs is a conformance matter too: on the household's own device or hub by default, and if any part runs remotely, only a declared minimal view leaves the home, with no retention and no training. The reference controller gathers minutes from the devices and network controls the household enrols, and it is permitted to observe only the app endpoints the plan names. It keeps no record of anything else, which is the difference between a timer and a wiretap.

One note on incentives. Every draft of this idea has used "twenty minutes for emptying the dishwasher" as its example of a grant. Paediatric guidance warns that using screens as a reward raises their value to the child ([American Academy of Pediatrics, Family Media Plan](https://www.healthychildren.org/English/media/Pages/default.aspx)). Grants stay in the standard, because parents will make them whatever the standard says, but the guide should flag reward-for-chores patterns and the default profiles should not model them.

## 4. The standard in plain words

Kerb is a vocabulary and a set of rules for exchanging screen policy between a household and a platform. Think IARC for ratings, or Matter for the smart home. It is not a product. It is the thing products must agree on.

### 4.1 Actors

- **The child.** The person the data is about. Sees every rule and every reason.
- **The guardians.** Parents or carers. Hold the only right to set and change policy.
- **The household controller.** Certified software in the home, on a phone, a hub or a router, that holds the policy and the ledger. The only place the child's full record exists.
- **The platform.** Any operating system, console, store or service a child uses. Receives the effects of a policy, applies them, reports back.
- **The guide.** An AI assistant working for the household. Optional. Certified like a platform. Reads only what the controller holds.
- **The community service.** A shared database of app tags and policy profiles, holding nothing about any child.
- **The steward.** The non-profit that publishes the standard, runs the certification mark, issues controller credentials and hosts the community service.
- **The regulator.** Publishes the statutory default profile for its jurisdiction, recognises the mark, may require it, and audits the steward.

### 4.2 What is exchanged

Three objects move between home and platform. Each has a part that crosses the home boundary and a part that never does.

A **policy**: the standing rules for one child. The part the platform receives is: a daily time budget, rounded to 15 minutes; allowed windows, in 30-minute slots; a bedtime; a ceiling on content rating; an age band in the shape of the Google Play Age Signals defaults (under 13, 13 to 15, 16 to 17, 18 and over), onto which Apple's Declared Age Range thresholds map ([Google Play Age Signals](https://developer.android.com/google/play/age-signals); [Apple](https://developer.apple.com/documentation/declaredagerange)); the guardian's declared country, so the platform can select the applicable floor; and rules keyed to app identifiers and content ratings. Effects are plain words: allow always, allow, count half, count double, require approval, block. A platform receives only the fields its declared capabilities can honour. Everything else stays home: milestones and their dates, progress against them, the guide's reasoning, rules keyed to community tags, which the controller resolves to app identifiers before anything is sent, and the exact budget the household set.

An **override**: one parental decision with a lifetime. The platform receives effect, scope and expiry: "lock, this account, until 18:00". The reason ("dinner") and who made it are recorded in the controller and shown to the child there, and never cross the boundary. Every override expires, by default at the end of the day. Open-ended rules are policy changes, not overrides, so a punishment cannot quietly become permanent.

A **result**: the platform's honest answer, read back from its own state. Applied, confirmed, partial, failed or unknown. If a platform could not do what was asked, it says so and says how it approximated.

Usage flows back as plain facts: this device, this app, these minutes. A child's request flows back as a structured signal, app identifier plus request type (play, more time, unlock), with no free text. The home turns facts into a ledger. The platform never sees the ledger.

Identifiers are pairwise. The controller derives a different child identifier for each platform, as OpenID Connect does with pairwise subject identifiers ([OpenID](https://openid.net/specs/openid-connect-core-1_0.html#PairwiseAlg)), and sends no household identifier at all. No two platforms receive the same string, and the coarsened budget and windows mean the plan itself is not a fingerprint either.

**The statutory default profile** is a policy object in the same shape, published by each participating regulator in the registry, versioned, signed and keyed by jurisdiction. Where no regulator has published one, the platform's existing under-age rules are the default and Kerb adds nothing.

### 4.3 What a platform, a controller and a guide must do to comply

A platform must:

- Accept a Kerb policy and override for a child's account from a controller whose credential the steward issued, verifying a signature and never a parent. The guardian is verified once, by the OS family account that already holds the age declaration, and the controller's credential chains from it. Credentials are revocable.
- Apply the statutory default profile for the account's jurisdiction to any child account with no household plan, selecting the jurisdiction from the plan's declared country combined with its own existing lawful geo signals.
- Apply the plan, read back its own state, and report the result honestly. Unknown is reported as unknown, never as unlocked. Silent failure is a conformance violation.
- Report usage to the household, per app where it can, and say when it cannot.
- Carry a child's structured request back to the household.
- Show the child a fixed system notice: "A household plan applies. Set by your guardian. Open your Kerb app for the reason." The reason, the actor and any disagreement live in the controller app, never on the platform's surface.
- Use what it receives through Kerb only to apply the plan, read back, log conformance, prevent abuse and security incidents, and run child-safety features. Never for advertising, ad measurement, cross-service profiling, sale or any sharing beyond the household. Read-back logs are kept pseudonymous, without content, for at most twelve months, so the platform can defend itself in a dispute.
- Never ask for a date of birth, an identity document or a location through the Kerb channel. The only age source is the guardian's existing OS family-account declaration, which Kerb consumes as a band. Existing lawful geo signals may be used to select the applicable floor.

A household controller must: observe the network only for the app endpoints the plan names, on an allow or deny list; retain no DNS or connection log beyond the minute counter; record per-device minutes only at Level 0; enrol a device only by explicit action visible to the child, never by passive discovery; exclude school-managed and employer-managed devices by default; and hold no platform credential. A controller that logs in as the parent and drives undocumented vendor endpoints is not certified. The reference implementation may offer such routes for a household's own use, outside the mark, storing any credential in the OS keychain, reading only the fields the plan needs and showing the child that the route exists.

A guide must: run on the household's device or hub by default; if any part is remote, receive only a declared minimal view (budget state, tag lookups, milestone names and dates), with no retention, no training and no third-party sharing; and be certified and listed like a platform.

Conformance has five levels so a router and a social network can both take part. Level 0, Observer, reports usage. Level 1, Cut-off, can stop now and release later and confirm it. Level 2, Budget, accepts a daily allowance and windows and confirms them by read-back. Level 3, Interactive, adds grants, child requests and per-app rules. Level 4, Native, accepts the objects at one endpoint and emits the standard events. Nobody is at Level 4 today. No major vendor exposes any parental-control interface. Where a match exists, field names mirror the Matter Content Control cluster so a certified Matter television can join without renaming, and the conformance route is designed to sit beside ISO/IEC 27566-1, the new age-assurance framework standard ([ISO](https://www.iso.org/standard/88143.html)).

### 4.4 What stays in the home

Two tiers. The **raw ledger**: every minute, grant, lock and reason, per child, per day, written so a parent can show it to a child in full. Deleted on a schedule the household chooses, default 31 days. Zero retention is valid. The **persistent summary**: milestone names and the dates a parent set them, nothing else. No counts, no streaks, no events. Anything the guide says about a pattern is computed from the raw ledger and is not stored.

Visibility tapers as control does. Until a milestone the household sets, by default Noticing, both parents and child see per-app detail. After it, parents see totals against budget and enforcement health only, and the child alone sees per-app detail. The full policy and the guide's reasoning stay in the controller. When a child leaves the plan, the child chooses export or deletion of the summary, the default is deletion, and every other record about them is deleted.

### 4.5 What never leaves

A child's name. A date of birth. A location, beyond the guardian's declared country. Credentials. Content, messages, browsing. Device identifiers. Per-app usage. Milestones and progress. Reasons and actors. Identifiers sent to a platform are unique to that platform. The only things a household may send to the community service, and only if a parent turns sharing on, are app identifiers and votes on tags, under per-vote anonymous tokens described in 4.6.

This is not rights rhetoric. It is how the standard meets the Children's Code, whose standard 11 requires that children know when they are monitored, and General Comment 25, which discourages covertly documenting a child's activity. Kerb documents overtly and shows the child. A platform receives a plan from a guardian, not a passport from a child. Apple's own white paper argued that store-wide age verification would force all users to hand over "sensitive personally identifying information" for a limited set of apps ([Apple, February 2025](https://developer.apple.com/support/downloads/Helping-Protect-Kids-Online-2025.pdf)). Google's public policy lead wrote in March 2025 that the Utah model creates new privacy risks for minors while not addressing the harms that drove lawmakers to act ([Pluribus News on Google's blog post, March 2025](https://pluribusnews.com/news-and-events/google-pitches-age-verification-alternative/)). The two vendors that would be first to implement Kerb have already made its privacy argument.

### 4.6 How community knowledge flows

Parents know things ratings boards do not. Kerb carries a curated vocabulary of about thirty tags in five groups: value (educational, creative, reading), social (friends-only, chat-with-strangers, voice-chat), commerce (in-app purchases, loot boxes), content, and attention (endless feed, autoplay, no stopping point, offline-ok). Households vote, one vote per household per tag per app, on MusicBrainz rules. Duplicate votes are rejected without any household identifier: the steward issues one blind-signed token per app, tag and epoch to each household, so votes are unlinkable across apps and epochs, and votes travel through a relay so no address is logged. A tag shows when its net score is positive. Caution tags need evidence and three contributors. Visible tags are capped at ten per app. A developer may dispute a tag on its own product; the steward reviews the evidence and the tag is suppressed pending review. Parents publish named profiles ("strict under 10", "educational first", "Swedish health guidance") and others subscribe. The local plan always wins. Tags are resolved to app identifiers inside the household controller and never reach a platform, so no platform need ingest the dataset. Data is open with a nightly dump, so the service is not a single point of failure and never sees a child. The licence is ODbL in the draft; a permissive licence such as ODC-By is under consideration so a platform could ingest the dump if it chose to. The service starts empty, so before launch the steward curates the 200 to 500 most-used children's apps against the vocabulary and marks those tags "curated" until household votes replace them. Where a tag has no votes the guide says so.

### 4.7 Certification

A platform runs a published, self-service test suite and submits the result, as OpenID Connect does; its own leaders credit cheap self-certification plus a public list with making Connect the most deployed identity protocol ([OpenID Foundation](https://openid.net/certification-accomplishments-and-next-steps/)). The steward lists certified implementations publicly with level, date and suite version. Suite versions are semantic: a minor version is backward compatible and never invalidates a listing; a major version gives a published 18-month migration window; a listing records the suite version it was tested against until its next annual re-test.

Field audit uses synthetic households only: the suite runs scripted test accounts against the live platform and the steward sees those traces. Platforms report field figures as counts (writes, confirmed, unknown, later found unlocked) with no identifiers or timestamps. A platform that fails the two field rules, confirming without read-back or showing unknown as unlocked, above a published threshold (for example unknown shown as unlocked on more than 1 per cent of locks over 30 days, measured from certified controllers only) receives written notice, a 90-day cure period and an independent appeal before delisting. Delisting is prospective and never voids compliance for the period the platform was listed. The list shows "notified" and "curing" states as well as "listed" and "delisted". Recognition across jurisdictions follows the IARC pattern: one certified result, accepted by every participating regulator ([IARC milestones](https://www.globalratings.com/milestones)).

## 5. Why each party gains

**The minister** keeps the sentence, the list and the fine, and adds a second sentence: "A parent-managed account on a certified platform may carry a graduated household plan." The floor covers the child nobody is helping. The path covers the child whose parents want to help. No parent-managed account needs a passport. The France challenge is narrowed to the accounts that carry neither a plan nor a band, and section 7 asks you to accept the band for those.

**The regulator** gets something auditable: a public registry, conformance levels, annual re-test, a published enforcement process, and a steward it can inspect. Ofcom's own first age-assurance report favours layered protection across devices, app stores and operating systems ([Ofcom, July 2026](https://www.ofcom.org.uk/siteassets/resources/documents/online-safety/information-for-industry/age-assurance-report-2026/report-on-the-use-of-age-assurance.pdf)). Kerb is that layered architecture written down.

**The Treasury and the trade department** get a mutual-recognition case. Fifteen jurisdictions now name different ages, different service lists, different tests of "highly effective" and different penalties, from A$49.5 million to 6 per cent of global turnover. Every platform answers every regulator alone. One certified mark recognised across jurisdictions, as IARC is for ratings, is a competitiveness argument a finance ministry will own.

**Parents** get one place to set rules for every screen, a guide that knows the games, and the loosening path they already want.

**Children** get a path with visible steps, a record they can read, a way to contest a rule, privacy from their parents that grows with them, and an end date.

**Platforms** get a shared bar and a safe harbour. "We support Kerb Level 2" is one sentence for fifteen regulators. An account that arrives with a recognised plan need not be age-verified by the platform, because the guardian's OS family account already holds the age declaration; the OS band plus the plan substitutes for a per-service ID check wherever the regulator accepts it. The saving depends on the share of child accounts that arrive managed, and no public figure for Apple or Google family-account penetration was found; the pilot should produce one. The OS vendors are the natural first implementers: Apple's Declared Age Range API ([Apple](https://developer.apple.com/documentation/declaredagerange)) and Google's Play Age Signals API ([Android Developers Blog, July 2026](https://android-developers.googleblog.com/2026/07/google-play-age-signals-api-safer-experiences.html)) already carry a parent-set age band to apps, off by default. Google's terms bar use of the signal for advertising, marketing, profiling or analytics ([Google Play Age Signals](https://developer.android.com/google/play/age-signals)); no equivalent public term was found for Apple. Kerb adds the plan that sits on top of the band. The ask is small: the channel that carries a band also carries a plan and returns a result.

## 6. Governance and funding of the steward

Standards that won vendor adoption against initial interest shared four features: a regulatory or liability tailwind that made the standard the cheaper route, as Global Privacy Control had after California's Sephora enforcement ([IAPP, 2022](https://iapp.org/news/a/california-attorney-general-announces-first-ccpa-enforcement-action)); an open reference implementation vendors could ship rather than build, as Matter had ([Matter](https://en.wikipedia.org/wiki/Matter_(standard))); a certification programme that made "compliant" checkable; and someone with a reason to pay. Do Not Track and P3P lacked all four and died ([W3C](https://www.w3.org/TR/tracking-dnt/)). Full notes are in research/standards-precedent.md.

Kerb's steward follows the pattern in three stages.

**Stage one, 2027.** A W3C Community Group, free to start and join, with a neutral IPR policy, so a platform engineer can participate without asking legal for a budget ([W3C](https://www.w3.org/community/about/design-goals/)). Specification, schemas, conformance suite and reference controller published under open licences. Running cost about 300,000 EUR a year, met by a named government pilot sponsor and one or two foundation sponsors.

**Stage two, 2028.** Once two independent implementations conform, a non-profit steward incorporated in Europe on the ISRG model, which runs Let's Encrypt and two other projects on about 7 million USD a year from sponsors and small donors ([ISRG](https://www.abetterinternet.org/annual-reports/)). The open-source reference controller counts as the first implementation; the first certified platform is the second. Running cost rises to about 600,000 EUR a year with the registry, audit and credential issuance, still under a tenth of ISRG. If the gate is not reached, the specification stays open in the Community Group.

**Stage three, 2029 onward.** Membership dues on the Connectivity Standards Alliance scale, 7,500 to 112,500 USD a year by tier ([CSA](https://csa-iot.org/become-member/)), with a permanent free tier for non-profits, academics and small developers, and certification fees of about 2,000 EUR per product. The arithmetic is slow: two members at the middle tier plus two certifications is under 50,000 USD a year. Dues cover 600,000 EUR only at roughly 25 members across tiers, which on this roadmap is 2031 at the earliest. A government and sponsor line stays through stage three until that member count exists.

Principles. A permanent child-rights seat and a permanent privacy seat on the board. Platform seats capped at half. The founding company holds at most one non-voting seat, its own products are certified by the same self-service suite and listed with the same disclosure as everyone else, and the community service's code and data are mirrored outside the company from day one. The steward never holds per-child data, never charges parents or children, and never sells data.

Honest weakness: Signal's foundation ran an 8.6 million USD deficit in 2024 on 29 million USD revenue ([ProPublica](https://projects.propublica.org/nonprofits/organizations/824506840)). Donation funding is fragile. Who pays before certification is a government, or nobody. Section 7 makes that a costed request rather than a confession.

## 7. What we ask, costed, and what you get for it

The UK ban is pencilled for spring 2027. The first certified platform cannot realistically exist before 2028. Nothing here asks you to wait or to repeal. Three asks fit the calendar.

1. **A future compliance route in secondary legislation now, with a safe harbour.** One clause: a parent-managed account governed by a certified graduated household plan, at a conformance level the regulator names, may be treated as meeting the minimum-age duty. A platform that applies a plan received from a steward-certified controller, and reads back honestly, has discharged that duty for that account; its other duties under the Act are unchanged. The clause also accepts the OS family account's parent-declared age band as a lawful age signal. It commits you to nothing until a mark exists. It gives platforms a reason to build toward it. Where the minimum age sits in primary legislation with no parental route, as in Australia, the same words need an amendment.
2. **A named pilot sponsorship.** Australia's trial of 60 technologies from 48 vendors was funded at A$6.5 million ([Australian Government, trial findings](https://minister.infrastructure.gov.au/wells/media-release/albanese-government-releases-age-assurance-technology-trial-findings); [Department of Social Services](https://www.dss.gov.au/national-plan-end-violence-against-women-and-children/progress/first-action-plan-progress/first-action-plan-activities-addendum/age-assurance-technologies-protect-children-harmful-online-content)). A sum of that order, about 3.5 million EUR, funds the following.

   | Item | Estimate |
   |---|---|
   | Steward, two years at 300,000 then 600,000 EUR | 900,000 EUR |
   | Reference controller and conformance suite, open source | 800,000 EUR |
   | Pilot, 400 households at about 2,000 EUR each (devices, support, incentives) | 800,000 EUR |
   | Independent, pre-registered evaluation by a university partner | 700,000 EUR |
   | Contingency | 300,000 EUR |
   | **Total** | **3.5 million EUR** |

   These are planning figures, not quotes. Pilot data is held by the university as data controller, with separate consent for each child and age-appropriate assent, no link between pilot records and the community service, and deletion at study end.
3. **A twelve-month review point** written into the ban's own commencement, at which the regulator reports on the pilot's outcomes beside the ban's.

What you get for it is the evidence nobody has. Of the 40 restriction experiments reviewed by Lind, Schueller and Odgers, none reported a mean participant age under 18 ([Lind, Schueller and Odgers, May 2026](https://www.frontiersin.org/articles/10.3389/fdpys.2026.1805989/full)). The pilot produces consented, minimal, longitudinal data on how children acquire screen competence, published whether or not it flatters the idea.

## 8. Three-year roadmap

**2027: the standard and the pilot.** Kerb 1.0 published as a Community Group draft with schemas, conformance rules and the tag vocabulary. Reference household controller released as open source, working over the device controls and allow-listed network controls that households already own. Advisory groups formed: child rights, privacy, parents, platforms, researchers from both camps. Government pilot sponsor named. Pilot design pre-registered with a university: outcome measures are sleep, self-reported wellbeing, media literacy, parent-child conflict and the six milestones, not account counts or minutes. The steward's curation of the first 200 to 500 apps against the vocabulary begins. Briefings to Ofcom, eSafety, the Commission's DSA minors team and the Swedish commission, each asked the same question: if a platform certified at Level 2, would you say so in guidance?

**2028: the first platform and the registry.** Conformance suite and public registry live. One OS vendor or console maker at Level 2, most likely one already carrying a parent-set age band or already in Matter. Community service live with curated tags, seeded with IARC age ratings and content descriptors, which do not supply the attention or social tags; those are curated. Steward incorporated in the fourth quarter, the reference controller and the first certified platform being the two conforming implementations. First pilot results published.

**2029: the regulator cites the mark.** One regulator, anywhere, names Kerb conformance in guidance, a code of practice or a procurement document. A second platform certified. Membership opens. First outcome report against the ban baseline.

If 2029 does not deliver a regulatory cite, the honest position is that the standard remains useful to the households that run it, and the specification stays open for whoever picks it up next.

## 9. Risks and objections, with answers

**"Parents want a ban."** Around nine in ten of the parents whose consultation answers were broken out did. Kerb does not take it from them. The floor stays. The path is for the parents who want more, and the default profile covers the children whose parents do not engage.

**"Platforms never adopt open standards voluntarily."** Correct. No vendor exposed an age signal until Texas and Utah made them. Kerb does not ask for goodwill. It rides the laws that already force parent-mediated channels and asks the regulator to name the mark. Until then the reference controller works over the household's own devices and allow-listed network controls, under the observation rules in 4.3, without anyone's permission.

**"Apple and Google already have age-range APIs, and could ship this themselves."** They are the foundation, not the competitor, and they could. Screen Time and Family Link are household controllers already. What neither can be is neutral: Apple will never control a PlayStation or a Windows PC, and no household is single-vendor. If one OS vendor ships a proprietary equivalent, a regulator still needs a mark that is not owned by one of the regulated, and the households still need the cross-vendor layer. The open specification and the open data are not what holds this together. Neutrality, the guide and the households are.

**"A parent signal can be faked."** So can a ban, and Australia shows how often. Kerb's floor is no weaker than the ban's; its path serves the willing majority. The pilot measures how many route around a plan they helped write.

**"The AI guide is surveillance."** It would be if it read content, or if it ran in a vendor's cloud on the whole ledger. The standard gives it no field for content, messages or location, requires it to run in the home by default, and certifies it. The ledger is visible to the child by design, which is what the Children's Code requires and what General Comment 25 asks for, and from Noticing the per-app detail is the child's alone. The weakness is real: a conformance mark constrains the standard, not what a vendor does beside it.

**"Competence milestones are a middle-class fantasy."** The strongest objection. Default profiles, a guide that does the thinking, and community profiles from households like one's own are the answers. They may not be enough. The pilot must include families across income, education and shared-device households, and the data must be published either way.

**"The competence tier is a proxy dressed as a measure."** Agreed, if it were a measure. It is a parental judgement the ledger informs, held only in the home. The pilot tests whether ledger patterns predict anything a researcher would accept.

**"Anonymous aggregate insight is still child data."** Agreed, so the steward publishes none. The registry shows platform and certification data only. The only longitudinal child data is the pilot's, held by the university under its own ethics approval, and it is never joined to the community service.

**"The evidence is too early to judge Australia."** Agreed. This paper says the early evidence is weak, not that the policy has failed. The review point in section 7 exists to judge both instruments on the same evidence.

**Weaknesses in our own evidence.** Several primary pages (eSafety, Ofcom, the BMJ, the Commission press corner, Apple's newsroom, Google's policy blog) blocked automated fetching, so figures were cross-checked against two secondary reports each and must be re-read from source before publication. The BMJ sample is 408 children in one state. VPN figures are vendor-reported. The parental mediation and sleep citations in section 3 were added in this synthesis and should be checked against the papers. The cost table in section 7 is a planning estimate. Leading academic critics of the harm thesis have industry advisory ties, which Appendix A discloses.

## 10. Call to action

To a minister: keep the floor. Add one clause for the path and its safe harbour, sponsor the pilot, set the review date.

To a regulator: tell us what a certified household-plan layer would need to look like for you to cite it, and publish your default profile in the registry. The conformance suite will be built to that.

To an OS vendor: the channel that carries an age band can carry a plan. Nominate one engineer to the Community Group.

To researchers and child-rights organisations: the under-18 evidence does not exist. Help design the instrument that produces it.

To parents: when your government offers you a ban, ask what happens at sixteen.

The ban is what you build when you cannot picture anything else. The diagrams and screens that accompany this paper picture it.

## Appendix A. The harm evidence, both sides

Kept out of the body because it is politically unusable and scientifically contested. The small-effects position: Orben and Przybylski found technology use explains at most 0.4 per cent of variance in adolescent wellbeing ([Nature Human Behaviour, 2019](https://www.nature.com/articles/s41562-018-0506-1)); Odgers' review found a mix of no, small and mixed associations, with evidence that struggling young people use platforms more rather than platforms causing the struggle ([Nature, 2024](https://www.nature.com/articles/d41586-024-00902-2)); Lind, Schueller and Odgers reviewed 40 restriction studies and found none with a mean participant age under 18, and disclose that Odgers advises YouTube and Schueller advises Headspace ([Frontiers, 2026](https://www.frontiersin.org/articles/10.3389/fdpys.2026.1805989/full)). The harm position: Braghieri, Levy and Makarin used Facebook's staggered college rollout to find a causal effect on mental health ([AER, 2022](https://www.aeaweb.org/articles?id=10.1257/aer.20211218)); Allcott and colleagues' deactivation experiment found modest wellbeing gains from a month off Facebook ([AER, 2020](https://www.aeaweb.org/articles?id=10.1257/aer.20190658)); Haidt's The Anxious Generation (2024) argues for a phone-based childhood as a cause of the adolescent mental-health decline. The one finding with consistent replication across camps is sleep displacement from bedtime device use ([Carter et al., 2016](https://doi.org/10.1001/jamapediatrics.2016.2341)), which is why bedtime is the rule Kerb protects first.

## Appendix B. Relationship to the technical draft

A phase-1 technical specification (Kerb 0.1: policies per child, overrides, tag-weighted usage, community tags, privacy rules) and an honest platform matrix showing that no vendor exposes a parental-control API exist as working documents. They are household-scale. The platform-facing Level 4 interface, the statutory default profile, the guide's data boundary, the controller observation rules and the certification mark are proposed here and not yet specified. No demo is offered because a half-working demonstration of what today's platforms permit would show less than this paper describes, and would be judged on what it cannot do.

## Appendix C. For funders

Kept out of the policy paper by design. The capital flows, competitive map, Swedish grant route, company structure, market sizing and exit analysis belong in FUNDING-LANDSCAPE.md, which is not revised in this draft. The short version, corrected. The steward, not any company, operates the standard's layer: the mark, the registry, the credentials and the community service. The company builds and sells a certified household controller and guide, as a paid household subscription from day one in 2027, working over the household's own devices and network before any platform adopts anything, and holding no copy of any ledger, which lives in the home. The steward's rule against charging parents binds the steward, not the company. The company's moat is not the open specification or the open data, which anyone may take. It is cross-vendor neutrality, the guide's quality, and the installed base of households. The regulatory cite in 2029 widens that moat; it is not the precondition for revenue. Inference cost for a guide that runs partly remote is the main variable cost and must appear in the commercial model. The standard, not the company, is what the regulator cites.

## Sources

- Jurist, UK under-16 ban announcement, June 2026: https://www.jurist.org/news/2026/06/starmer-sets-spring-2027-target-for-under-16-social-media-ban/
- Medianama, UK consultation takeaways, June 2026: https://www.medianama.com/2026/06/223-why-uk-banning-social-media-under-16s-takeaways-public-consultation/
- TechCrunch, countries with child social media age limits, July 2026: https://techcrunch.com/2026/07/21/social-media-ban-children-countries-list/
- European Commission, EU age verification and KIDS Act: https://digital-strategy.ec.europa.eu/en/policies/eu-age-verification
- Children's Wellbeing and Schools Act 2026, section 70 (inserting OSA s.214A): https://www.legislation.gov.uk/ukpga/2026/21/section/70
- DLA Piper, Online Safety Act minimum-age power, April 2026: https://www.dlapiper.com/en-hu/insights/publications/2026/04/online-safety-act
- Online Safety Amendment (Social Media Minimum Age) Act 2024 (Australia): https://www.legislation.gov.au/C2024A00127/asmade/text
- eSafety, 4.7 million accounts restricted, January 2026: https://esafety.gov.au/newsroom/media-releases/platforms-restrict-access-to-47-million-under-16-accounts-across-australia
- eSafety, compliance update, March 2026: https://www.esafety.gov.au/sites/default/files/2026-03/SocialMediaMinimumAgeComplianceUpdateMarch2026.pdf
- Al Jazeera, eSafety three-month survey, August 2026: https://www.aljazeera.com/news/2026/8/1/most-australian-teens-still-online-three-months-after-under-16-ban
- Reuters via TBS News, eSafety survey, July 2026: https://www.tbsnews.net/tech/most-australian-teens-still-social-media-three-months-after-under-16-ban-began-study-finds
- The National, BMJ study summary, June 2026: https://www.thenationalnews.com/future/technology/2026/06/25/age-verification-flaws-undermine-australias-social-media-ban-for-under-16s/
- Ofcom, Report on the Use of Age Assurance, July 2026: https://www.ofcom.org.uk/siteassets/resources/documents/online-safety/information-for-industry/age-assurance-report-2026/report-on-the-use-of-age-assurance.pdf
- LCP, Conseil constitutionnel decision, August 2026: https://lcp.fr/actualites/reseaux-sociaux-pourquoi-le-conseil-constitutionnel-a-censure-l-interdiction-pour-les
- 9to5Mac, Texas app-store law enjoined, December 2025: https://9to5mac.com/2025/12/23/texas-judge-blocks-state-app-store-age-verification-law/
- EFF, When no ID means no internet, October 2026: https://www.eff.org/deeplinks/2026/10/when-no-id-means-no-internet-age-verification-and-right-access-information
- The Record, Discord vendor breach, October 2025: https://therecord.media/discord-government-docs-exposed-breach
- The Register, Discord photo IDs leaked, October 2025: https://www.theregister.com/2025/10/09/discord_photo_ids_leaked/
- The Record, Tea app breach, July 2025: https://therecord.media/tea-app-data-breach-stolen-ids-leaked
- Australian Government, Age Assurance Technology Trial final report, August 2025: https://www.infrastructure.gov.au/department/media/publications/age-assurance-technology-trial-final-report
- Australian Government, trial findings release: https://minister.infrastructure.gov.au/wells/media-release/albanese-government-releases-age-assurance-technology-trial-findings
- Department of Social Services, age assurance trial funding (A$6.5 million): https://www.dss.gov.au/national-plan-end-violence-against-women-and-children/progress/first-action-plan-progress/first-action-plan-activities-addendum/age-assurance-technologies-protect-children-harmful-online-content
- The Register, UK VPN demand, July 2025: https://www.theregister.com/2025/07/28/uk_vpn_demand_soars/
- TechSpot, Sensor Tower VPN chart data, Australia, March 2026: https://www.techspot.com/news/111607-vpn-downloads-surge-australia-after-age-checks-hit.html
- TechRadar, Australian VPN surge, March 2026: https://www.techradar.com/vpn/vpn-privacy-security/vpns-surge-in-australia-as-mandatory-age-verification-for-adult-content-begins
- UNCRC General Comment 25, 2021: https://www.ohchr.org/en/documents/general-comments-and-recommendations/general-comment-no-25-2021-childrens-rights-relation
- ICO, Age Appropriate Design Code: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/childrens-information/childrens-code-guidance-and-resources/age-appropriate-design-a-code-of-practice-for-online-services/
- 5Rights, access limitations position, February 2026: https://5rightsfoundation.com/access-limitations-must-be-part-of-age-appropriate-design-and-effectively-restrict-companies-from-exploiting-children/
- Livingstone and Helsper, Parental mediation of children's internet use, 2008: https://doi.org/10.1080/08838150802437396
- Livingstone et al., Maximizing opportunities and minimizing risks, 2017: https://doi.org/10.1111/jcom.12277
- EU Kids Online: https://www.lse.ac.uk/media-and-communications/research/research-projects/eu-kids-online
- Carter et al., portable screen devices and sleep, JAMA Pediatrics 2016: https://doi.org/10.1001/jamapediatrics.2016.2341
- American Academy of Pediatrics, Family Media Plan: https://www.healthychildren.org/English/media/Pages/default.aspx
- ISO/IEC 27566-1:2025: https://www.iso.org/standard/88143.html
- OpenID Connect Core, pairwise subject identifiers: https://openid.net/specs/openid-connect-core-1_0.html#PairwiseAlg
- Apple, Helping Protect Kids Online, February 2025: https://developer.apple.com/support/downloads/Helping-Protect-Kids-Online-2025.pdf
- Apple, Declared Age Range API: https://developer.apple.com/documentation/declaredagerange
- Pluribus News, Google pitches age verification alternative (Ghanem blog post), March 2025: https://pluribusnews.com/news-and-events/google-pitches-age-verification-alternative/
- Google Play Age Signals overview and terms: https://developer.android.com/google/play/age-signals
- Android Developers Blog, Play Age Signals API, July 2026: https://android-developers.googleblog.com/2026/07/google-play-age-signals-api-safer-experiences.html
- OpenID Foundation, certification accomplishments: https://openid.net/certification-accomplishments-and-next-steps/
- IARC milestones: https://www.globalratings.com/milestones
- IAPP, first CCPA enforcement action (Sephora), 2022: https://iapp.org/news/a/california-attorney-general-announces-first-ccpa-enforcement-action
- Matter standard: https://en.wikipedia.org/wiki/Matter_(standard)
- W3C, Tracking Preference Expression (DNT) Note: https://www.w3.org/TR/tracking-dnt/
- W3C Community Groups design goals: https://www.w3.org/community/about/design-goals/
- ISRG annual reports: https://www.abetterinternet.org/annual-reports/
- Connectivity Standards Alliance membership: https://csa-iot.org/become-member/
- ProPublica, Signal Technology Foundation filings: https://projects.propublica.org/nonprofits/organizations/824506840
- Lind, Schueller and Odgers, Frontiers in Developmental Psychology, May 2026: https://www.frontiersin.org/articles/10.3389/fdpys.2026.1805989/full
- Orben and Przybylski, Nature Human Behaviour, 2019: https://www.nature.com/articles/s41562-018-0506-1
- Odgers, Nature, 2024: https://www.nature.com/articles/d41586-024-00902-2
- Braghieri, Levy and Makarin, AER, 2022: https://www.aeaweb.org/articles?id=10.1257/aer.20211218
- Allcott et al., AER, 2020: https://www.aeaweb.org/articles?id=10.1257/aer.20190658
- Research notes: research-policy.md, research/privacy-ageverif.md, research/standards-precedent.md, FUNDING-LANDSCAPE.md in this directory.
