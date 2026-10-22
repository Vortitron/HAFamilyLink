# Annex: What outside software can do with vendors' parental controls today

## What this adds

The main paper says that no major vendor offers other apps a way into its parental controls. This annex tests that claim against each vendor's own developer documents, as they stood on 22 October 2026. The picture is mixed. Apple does offer a public, approved route: an outside app can set limits and block apps on a child's iPhone or iPad, with a parent's approval. But it works only on the device itself, and the usage it sees cannot leave the device. Google, Microsoft, Nintendo, Sony and the large social platforms offer no such route that we could find. What has grown fast since 2025 is the other direction: operating systems now pass a parent-set age band, and news of a parent's approval or refusal, to apps. These are the nearest thing today to Handrail's "policy" and "result" messages. Matter's television parental controls exist but are still marked provisional. The annex ends with what Handrail could do now, and what needs vendors to add.

## How to read this annex

A few terms first.

- An **API** (application programming interface) is a published, supported way for one piece of software to ask another to do something.
- An **entitlement** is a permission a vendor must grant before an app may use a sensitive API.
- **Read back** means the outside app can check what actually happened, not just send an instruction. Handrail's "result" message depends on this.
- **Across family or devices** means one instruction reaches more than one device, or more than one child, without a separate install on each.

Each section asks five questions: what an outside app can read, what it can set, whether it can read the result back, whether it reaches across devices or family members, and what approval it needs. Not finding a public API is not proof that none exists, and vendors may hold unpublished partner deals.

## Operating systems

### Apple (iPhone, iPad, Mac)

Apple's "Screen Time API" is three frameworks that work together.

- **FamilyControls** handles permission. An app asks to provide parental controls. For a child, "a parent or guardian in the same Family Sharing group" must approve on the child's device. The child then cannot delete the app, and cannot sign out of iCloud while the app is authorised ([Apple, FamilyControls, read 22 October 2026](https://developer.apple.com/documentation/familycontrols)).
- **ManagedSettings** sets restrictions. With the user's permission, an app "can limit media showings, restrict app purchases, lock passcode settings, and configure other device behavior" ([Apple, ManagedSettings, read 22 October 2026](https://developer.apple.com/documentation/managedsettings)). This is also the framework that puts a block screen over chosen apps and websites.
- **DeviceActivity** watches time. An app can set a schedule, such as bedtime, and a time threshold for chosen apps or websites. Its extension can be warned before a schedule starts or ends, or as an activity nears its threshold, and the app can warn the person once the threshold is reached ([Apple, DeviceActivity, read 22 October 2026](https://developer.apple.com/documentation/deviceactivity)).

**What it can read.** Very little in plain form. Apps, categories and websites a parent picks come back as "opaque values", so the app does not learn which apps were chosen ([Apple, FamilyActivityPicker, read 22 October 2026](https://developer.apple.com/documentation/familycontrols/familyactivitypicker)). Usage reports are drawn inside a sealed extension. Apple says this sandbox "prevents your extension from making network requests or moving sensitive content outside the extension's address space" ([Apple, DeviceActivityReport, read 22 October 2026](https://developer.apple.com/documentation/deviceactivity/deviceactivityreport)). The same page says the report can draw on the user's own device or on "the device(s) of children in their iCloud family". So the child's minutes can be shown on screen, but not sent to a server or another vendor's app.

**Read back.** Partly. An app can inspect its own settings. But Apple warns that "the system doesn't guarantee that the settings you specify govern the device's behavior", because "the system is responsible for determining its effective state based on all the settings it receives" ([Apple, ManagedSettingsStore, read 22 October 2026](https://developer.apple.com/documentation/managedsettings/managedsettingsstore)). A threshold event tells the app a limit was reached. We could not confirm whether that one fact may then be passed to a server.

**Across devices and family.** Limited. The store "applies settings to the current user or device" ([Apple, ManagedSettingsStore](https://developer.apple.com/documentation/managedsettings/managedsettingsstore)), so the app must be installed and approved on each child device. A parent's device can open the app picker and see apps from "authorized child devices within the Family Sharing Group", and app tokens can be used by devices in the same Family Sharing group ([Apple, FamilyActivityPicker](https://developer.apple.com/documentation/familycontrols/familyactivitypicker); [Apple, ApplicationToken, read 22 October 2026](https://developer.apple.com/documentation/managedsettings/applicationtoken)). The framework pages list iPhone, iPad and Mac Catalyst (iPad-style apps running on a Mac). The pages for asking permission and for the app picker list only iPhone and iPad ([Apple, AuthorizationCenter, read 22 October 2026](https://developer.apple.com/documentation/familycontrols/authorizationcenter)). We found no support for native Mac apps. The ManagedSettingsStore page also lists tvOS 26 (Apple TV); we did not explore what that covers.

**Approval.** The app maker must ask Apple for the Family Controls entitlement before release, and make the same request for each Screen Time extension. Apple reviews the app first ([Apple, Requesting the Family Controls entitlement, read 22 October 2026](https://developer.apple.com/documentation/familycontrols/requesting-the-family-controls-entitlement)).

**Age and approval signals.** The Declared Age Range API, from iOS 26 and macOS 26, lets an app ask for a person's age range. For a child in Family Sharing, a parent or guardian decides whether to share it always, ask the child each time, or never. It uses its own entitlement, switched on as a capability in Apple's developer tools ([Apple, Declared Age Range, read 22 October 2026](https://developer.apple.com/documentation/declaredagerange)). The app sets its own age cut-offs, and "the system may override your age gates based on the local regulations" of the person's location ([Apple, AgeRangeService, read 22 October 2026](https://developer.apple.com/documentation/declaredagerange/agerangeservice)). From 4 June 2026, for new Apple Accounts in Texas, Apple also requires a parent's consent for a minor's downloads, in-app purchases and "significant changes" to an app. App makers flag significant changes through an API in PermissionKit, and can receive a server notice "that consent has been withdrawn for their app" ([Apple Developer News, 3 June 2026](https://developer.apple.com/news/?id=sg176nne)).

**iOS 27.** In June 2026 Apple previewed Time Allowances by app category and daily Schedules for parents ([Apple Newsroom, 8 June 2026](https://www.apple.com/newsroom/2026/06/apple-previews-new-child-safety-features/)). Its September 2026 release note confirms Time Allowances in iOS 27, iPadOS 27 and macOS 27 ([Apple Newsroom, 14 September 2026](https://www.apple.com/newsroom/2026/09/apples-new-child-safety-features-now-available/)). Neither page names a new parental-control API for developers. The June page mentions only existing tools, such as the Declared Age Range API and PermissionKit.

### Google (Android, Chromebook, Family Link)

**Family Link.** We found no public API that lets an outside app read or change Family Link settings. Google's family help pages cover what third-party apps may ask of a child's account, not a way in for other parental apps ([Google Families Help, read 22 October 2026](https://support.google.com/families/answer/9204736)). Family Link limits are per device: "if you set a daily limit of 2 hours, your child would get 2 hours of time on each device" ([Google Families Help, read 22 October 2026](https://support.google.com/families/answer/7103340)).

**Android itself.** Outside parental apps on Android rely on general tools rather than a supervision API.

- **Usage access.** Android's usage statistics service "provides access to device usage history and statistics". The user "still needs to grant permission through the Settings application" ([Android Developers, UsageStatsManager, read 22 October 2026](https://developer.android.com/reference/android/app/usage/UsageStatsManager)). We found no separate public "Digital Wellbeing API".
- **Accessibility service.** Many blocking apps watch the screen through Android's accessibility service. Google Play's policy says only tools built to help people with disabilities may call themselves accessibility tools, and it lists "monitoring apps" as an example of apps that are not. Other apps using the service must show a clear disclosure in the app and get the user's consent ([Google Play Console Help, read 22 October 2026](https://support.google.com/googleplay/android-developer/answer/10964491)).
- **Device management.** The Android Management API, which can lock down a whole device, is "restricted solely to commercial Enterprise Mobility Management (EMM) developers", with narrow uses also allowed for device-trust providers and phone makers ([Google, Android Management API permissible usage, updated 30 March 2026](https://developers.google.com/android/management/permissible-usage)). It is not open to consumer parental apps.

**Play Age Signals.** This is Google's age channel to apps. It returns a lower and upper age, a source tier (for example "managed by a parent or a guardian"), a status for parental approval of "significant changes" (approved, pending or declined), and an install code used to tell the app when a parent revokes approval ([Android Developers, Understand age signals responses, updated 21 July 2026](https://developer.android.com/google/play/age-signals/understand-age-signals-responses)). The default bands are 0 to 12, 13 to 15, 16 to 17 and 18 and over ([Android Developers, Use the Age Signals API, updated 20 July 2026](https://developer.android.com/google/play/age-signals/use-age-signals-api)). These match the bands in the main paper. It is still in beta, app makers must request access, and the data may be used only "to provide age-appropriate content and experiences", not for advertising, profiling or analytics. It returns signals for Brazil from 17 March 2026 and for Texas accounts created after 28 May 2026 ([Android Developers, Age Signals overview, updated 20 July 2026](https://developer.android.com/google/play/age-signals/overview)). Parents control sharing in Family Link, and "age ranges are never shared by default". Google said in July 2026 that it would launch in Australia and Canada by mid-August and reach all users worldwide "later this year" ([Android Developers Blog, 29 July 2026](https://android-developers.googleblog.com/2026/07/google-play-age-signals-api-safer-experiences.html)). That may have happened since; we did not confirm it.

### Microsoft (Windows, Family Safety)

We found no public Family Safety API. The only direct statement we found is from 2014, by a poster who said they were a developer on the Family Safety team: "currently there is no public API for Family Safety" ([Microsoft Q&A, September 2014](https://learn.microsoft.com/en-us/answers/a/3737335)). It is old and unofficial. Screen time is set for each device separately, for Windows, Xbox and Android ([Microsoft Support, read 22 October 2026](https://support.microsoft.com/help/4028244)). Web filtering works only in supported browsers (currently Edge), and other browsers are blocked "so that filtering cannot be bypassed" ([Microsoft Support, read 22 October 2026](https://support.microsoft.com/en-us/family-safety/filter-websites-and-searches-using-microsoft-family-safety)).

## Games consoles

### Xbox

Xbox has no outside parental API that we found. It does have a strong rule for games. Under certification rule XR-045, games "must check the XBOX network service for privileges" before multiplayer, chat, user-made content and similar features, and must respect child account settings. A child can ask, through a system screen, for a parent to allow the feature in one game ([Xbox certification XR-045, version 2.0, 1 March 2023](https://devdocs.xbox.com/publishing/certification/xr/xr-045)). This is a working model of "the platform holds the parent's rule and every app obeys it", though only inside Xbox.

### Nintendo Switch and Switch 2

The Parental Controls app sets a daily play limit for the console, can suspend a game when time runs out, filters by age rating, limits chat and spending, and on Switch 2 means players under 16 can use GameChat only with friends a parent has approved ([Nintendo, read 22 October 2026](https://www.nintendo.com/us/switch/parental-controls/)). We found no public API for outside apps.

### PlayStation

Sony's controls are "tied to accounts" and cover playtime, age levels, chat, web browsing and a monthly spending limit (set to zero by default). They are managed in the PlayStation Family app, on the account website or on the console ([PlayStation Support, read 22 October 2026](https://www.playstation.com/en-gb/support/account/ps5-parental-controls-spending-limits/)). We found no public API for outside apps.

## Social and video platforms

None of the five platforms below publishes an API that lets an outside parental app read or set its teen controls, as far as we could find. Each has its own in-app parent tool.

| Platform | What a linked parent can set in the vendor's tool | Outside API found | Source |
|---|---|---|---|
| Meta (Instagram, Facebook, Quest) | Daily limit, sleep mode, see who the teen follows; on Quest, breaks and app approval by age rating. No message content | None | [Meta Family Center, read 22 October 2026](https://familycenter.meta.com/supervision/) |
| TikTok | Different daily limits for weekdays and weekends, "Time Away" schedules, see followers and blocked accounts; 60 minute default for under 18s | None | [TikTok Newsroom, 12 March 2025](https://newsroom.tiktok.com/ph-teen-well-being-and-family-pairing-updates?lang=en-PH) |
| YouTube | Daily limit for the Shorts feed, down to zero | None | [YouTube Blog, 26 January 2026](https://blog.youtube/inside-youtube/a-decade-of-building-for-teens-and-families/) |
| Roblox | Block single games and manage chat up to age 15; approve games outside the account's default; new Kids (5 to 8) and Select (9 to 15) accounts from early June 2026 | None for parents. Game makers can read some per-player policy flags, such as whether paid random items are restricted | [Roblox Newsroom, 13 April 2026](https://about.roblox.com/newsroom/2026/04/introducing-roblox-kids-and-select-accounts); [Roblox Creator Docs, PolicyService, read 22 October 2026](https://create.roblox.com/docs/reference/engine/classes/PolicyService) |
| Discord | Who can message the teen, sensitive content filter; weekly view of purchases, call minutes and top contacts. No message content; no time limit mentioned | None | [Discord, 5 November 2025](https://discord.com/safety/family-center-is-getting-an-update) |

These limits live inside each app, so they do not add up with time elsewhere. Today an outside controller reaches these apps only through the phone's operating system, which can block or time-limit them.

## Television: Matter's Content Control cluster

Matter is the shared smart-home standard run by the Connectivity Standards Alliance. A "cluster" is one named set of controls in it. The Content Control cluster is for "managing the content control (including "parental control") settings on a media device such as a TV, or Set-top Box" ([Matter reference code, Content Control cluster, last changed 23 October 2025](https://github.com/project-chip/connectedhomeip/blob/master/src/app/zap-templates/zcl/data-model/chip/content-control-cluster.xml)).

It defines a daily screen time and the remaining time, bonus time, a PIN, age-rating limits for on-demand and broadcast content, blocking unrated content, blocked channels, blocked apps and blocked time windows. The TV raises an event when time runs out and when a blocked window starts. A controller can read the settings back. Changing or resetting the PIN, and switching the controls on or off, need a "timed" request, a Matter safeguard against delayed or replayed messages.

Two cautions for the main paper. Every feature in the reference code is marked "provisional", meaning it is not yet final. And a third-party directory of Matter products, which dates the cluster to Matter 1.3, lists no certified product that supports it ([Matter Alpha, read 22 October 2026](https://www.matteralpha.com/cluster/content-control)). Amazon says Fire TV implements Matter casting, but its list of supported clusters does not include Content Control ([Amazon Developer, read 22 October 2026](https://developer.amazon.com/docs/fire-tv/overview-of-matter-casting.html)). So "a certified Matter television can join without changes" is the right aim, but not yet true. The cluster knows a device, not a child.

## Home network: routers and DNS

DNS (the Domain Name System) is the internet's address book. A filtering DNS service refuses to look up blocked sites. Cloudflare's family service blocks sites linked to malware and phishing, and optionally adult content ([Cloudflare, updated 6 May 2026](https://developers.cloudflare.com/1.1.1.1/setup/)). Some paid services have a full API. NextDNS, for example, lets a holder of the account's key change parental settings (blocked services, categories, safe search, YouTube restricted mode) and read logs and statistics by device ([NextDNS API, read 22 October 2026](https://nextdns.github.io/api/)).

DNS sees website names, not apps or minutes. It cannot tell a child from a parent on the same device. And a device can send lookups inside encrypted web traffic instead (DNS over HTTPS, [IETF RFC 8484, October 2018](https://www.rfc-editor.org/rfc/rfc8484)), which skips the home filter unless the device or browser is set to respect it. A router fits Handrail levels 0 and 1, "observe" and "cut off", and little more.

## Summary table

| Vendor or layer | Outside app can read | Outside app can set | Read back | Across devices or family | Approval needed |
|---|---|---|---|---|---|
| Apple iOS and iPadOS | Opaque app tokens; usage shown only on screen | Blocks, schedules, time thresholds, some restrictions | Own settings; "limit reached" events | One install per child device; parent can pick apps from the family | Family Controls entitlement; parent approval on device |
| Apple age and consent | Age range if parent allows; consent withdrawn notice | Nothing | Not applicable | Per account | Declared Age Range entitlement |
| Google Family Link | Nothing found | Nothing found | No | No | None available |
| Android (general) | App usage with user grant | Blocking via accessibility, with disclosure | Own state only | One install per device | Play policy; enterprise API closed to consumers |
| Google Play Age Signals | Age band, source, approval status, revocation | Nothing | Not applicable | Per account | Access request to Google; beta |
| Microsoft Family Safety | Nothing found | Nothing found | No | No | None available |
| Xbox | Games check privileges | Nothing | Not applicable | Per account | Xbox certification |
| Nintendo, PlayStation | Nothing found | Nothing found | No | No | None available |
| Meta, TikTok, YouTube, Roblox, Discord | Nothing found for parental tools | Nothing found | No | No | None available |
| Matter TV | Settings and remaining time | Time, ratings, blocks, bonus | Yes | One TV | Matter certification; cluster provisional |
| DNS service with API | Lookups by device | Blocked sites and categories | Yes | Whole home network | Account key |

## Laws that are opening doors

Three laws or bills push vendors in Handrail's direction. Each may have moved since we read it.

- **Texas SB 2420** has applied to new accounts since late May and early June 2026, after a court lifted an injunction. It is why Apple and Google now pass parental consent and revocation to app makers ([Apple Developer News, 3 June 2026](https://developer.apple.com/news/?id=sg176nne); [Android Developers, Age Signals overview](https://developer.android.com/google/play/age-signals/overview)).
- **California AB 1043**, the Digital Age Assurance Act, was signed on 13 October 2025 and applies from 1 January 2027. Operating systems must ask for an age or birth date at account setup and, on request, send apps an age band through a "real-time API": under 13, 13 to 15, 16 to 17 and 18 and over. We could not open the official bill text and rely on a law firm's summary ([Alston & Bird, 23 October 2025](https://www.alstonprivacy.com/california-enacts-digital-age-verification-law/)).
- **Sammy's Law (US Senate bill S. 4159)** was introduced on 20 March 2026 by Senator Jon Husted, with Senators Katie Britt and Mark Warner. It would make social media platforms with more than 100 million monthly users, or over 1 billion dollars a year in revenue, offer "real-time" APIs to third-party safety software registered with the Federal Trade Commission. A child under 17, or a parent for a child under 13, could let that software manage the child's online interactions and account settings, but only to protect the child from harm ([US Congress, S. 4159 text on GovInfo, March 2026](https://www.govinfo.gov/content/pkg/BILLS-119s4159is/xhtml/BILLS-119s4159is.html)). We found no record that it has passed. An earlier House version from 2023, H.R. 5778, is shown as only introduced ([Tech Policy Press tracker](https://techpolicy.press/tracker/sammys-law-of-2023-hr5778)).

Sammy's Law is the closest existing text to Handrail's demand that platforms accept any certified controller. But it moves the child's data out to the outside software. Handrail sends rules in and keeps data at home.

## What Handrail could do today, in plain words

**Could run now, on Apple phones and tablets.** An independent Handrail controller could be built today as an approved Screen Time app. It could hold the plan and apply bedtime, allowed hours, blocked apps and websites, and a daily limit on chosen apps, on each child's iPhone and iPad. It would need Apple's entitlement and an install on each device. It could not send minutes to other vendors' devices, so "two hours in total across all screens" cannot be counted from Apple's data.

**Could run now, on Android, with caveats.** A controller could read app use and block apps, using usage access and the accessibility service. This is fragile, rests on tools Google polices, and Family Link never knows.

**Could run now, on the home network and TVs.** A home hub could apply allowed hours and blocked sites through a filtering DNS service, and record which devices were online. A Matter television that supports Content Control could take a daily limit, ratings and blocks, and report remaining time. We found none on sale.

**Could run now, as an age band.** The age-band part of a Handrail policy already travels to apps on both Apple and Google, with the parent in charge of sharing. On Google this is not yet available everywhere.

**Needs the vendor to add something.**

- **Google, Microsoft, Nintendo and Sony:** a supported way to accept a plan from an outside controller and say back what was applied. Today there is none that we found.
- **Apple:** a way for a controller to receive plain usage facts, such as minutes per category per day, with the parent's permission, so time can be counted across vendors. And one install that covers all of a child's Apple devices.
- **Meta, TikTok, YouTube, Roblox and Discord:** a way to accept a daily budget, hours and "lock until" orders for a child's account, and to report back. The Xbox rule that every game must check the parent's settings shows this can be made a condition of access.
- **Apple and Google together:** carry the plan, not just the age band, down the same channel they already use for age and consent. This is the "small ask" in the main paper, and the Texas consent work shows the pipe exists.
- **Matter:** move Content Control out of provisional status, and add a notion of which child is watching.

## Open questions

- Can a Screen Time "limit reached" event lawfully be sent to a server, under Apple's rules, so a controller can share it with other devices? Apple's documents do not say clearly.
- Has Google's Play Age Signals reached Sweden and the rest of the EU since July 2026?
- Does Microsoft still hold that there is no public Family Safety API? The only statement we found dates from 2014.
- Does any television on sale in Sweden support Matter Content Control?
- Do any vendors have private partner routes into their parental controls that are not published?
- Will Sammy's Law or California AB 1043 change before 2027, and will the EU's KIDS Act require something similar?

## Sources

All pages read on 22 October 2026 unless a date is given.

- [Apple, FamilyControls](https://developer.apple.com/documentation/familycontrols)
- [Apple, AuthorizationCenter](https://developer.apple.com/documentation/familycontrols/authorizationcenter)
- [Apple, FamilyActivityPicker](https://developer.apple.com/documentation/familycontrols/familyactivitypicker)
- [Apple, Requesting the Family Controls entitlement](https://developer.apple.com/documentation/familycontrols/requesting-the-family-controls-entitlement)
- [Apple, ManagedSettings](https://developer.apple.com/documentation/managedsettings)
- [Apple, ManagedSettingsStore](https://developer.apple.com/documentation/managedsettings/managedsettingsstore)
- [Apple, ApplicationToken](https://developer.apple.com/documentation/managedsettings/applicationtoken)
- [Apple, DeviceActivity](https://developer.apple.com/documentation/deviceactivity)
- [Apple, DeviceActivityReport](https://developer.apple.com/documentation/deviceactivity/deviceactivityreport)
- [Apple, Declared Age Range](https://developer.apple.com/documentation/declaredagerange)
- [Apple, AgeRangeService](https://developer.apple.com/documentation/declaredagerange/agerangeservice)
- [Apple, PermissionKit](https://developer.apple.com/documentation/permissionkit)
- [Apple Developer News, Update for Apps Distributed in Texas, 3 June 2026](https://developer.apple.com/news/?id=sg176nne)
- [Apple Newsroom, Apple previews new child safety features, 8 June 2026](https://www.apple.com/newsroom/2026/06/apple-previews-new-child-safety-features/)
- [Apple Newsroom, Apple's new child safety features now available, 14 September 2026](https://www.apple.com/newsroom/2026/09/apples-new-child-safety-features-now-available/)
- [Google Families Help, Third-party sites and apps with access to your child's account](https://support.google.com/families/answer/9204736)
- [Google Families Help, Manage your child's screen time](https://support.google.com/families/answer/7103340)
- [Android Developers, UsageStatsManager](https://developer.android.com/reference/android/app/usage/UsageStatsManager)
- [Google Play Console Help, Use of the AccessibilityService API](https://support.google.com/googleplay/android-developer/answer/10964491)
- [Google, Android Management API permissible usage, 30 March 2026](https://developers.google.com/android/management/permissible-usage)
- [Android Developers, Play Age Signals overview, 20 July 2026](https://developer.android.com/google/play/age-signals/overview)
- [Android Developers, Use the Play Age Signals API, 20 July 2026](https://developer.android.com/google/play/age-signals/use-age-signals-api)
- [Android Developers, Understand age signals responses, 21 July 2026](https://developer.android.com/google/play/age-signals/understand-age-signals-responses)
- [Android Developers Blog, Delivering safer, age-appropriate experiences on Google Play, 29 July 2026](https://android-developers.googleblog.com/2026/07/google-play-age-signals-api-safer-experiences.html)
- [Microsoft Q&A, Is there a Family Safety API?, September 2014](https://learn.microsoft.com/en-us/answers/a/3737335)
- [Microsoft Support, Set screen time limits across devices](https://support.microsoft.com/help/4028244)
- [Microsoft Support, Filter websites and searches](https://support.microsoft.com/en-us/family-safety/filter-websites-and-searches-using-microsoft-family-safety)
- [Xbox certification requirement XR-045, 1 March 2023](https://devdocs.xbox.com/publishing/certification/xr/xr-045)
- [Nintendo, Parental Controls](https://www.nintendo.com/us/switch/parental-controls/)
- [PlayStation Support, PS5 parental controls and spending limits](https://www.playstation.com/en-gb/support/account/ps5-parental-controls-spending-limits/)
- [Meta Family Center, Supervision](https://familycenter.meta.com/supervision/)
- [TikTok Newsroom, New ways we're supporting parents and helping teens build balanced digital habits, 12 March 2025](https://newsroom.tiktok.com/ph-teen-well-being-and-family-pairing-updates?lang=en-PH)
- [YouTube Blog, A decade of building for teens and families, 26 January 2026](https://blog.youtube/inside-youtube/a-decade-of-building-for-teens-and-families/)
- [Roblox Newsroom, Roblox Kids and Select accounts, 13 April 2026](https://about.roblox.com/newsroom/2026/04/introducing-roblox-kids-and-select-accounts)
- [Roblox Creator Docs, PolicyService](https://create.roblox.com/docs/reference/engine/classes/PolicyService)
- [Discord, Family Center is getting an update, 5 November 2025](https://discord.com/safety/family-center-is-getting-an-update)
- [Matter reference code, Content Control cluster, last changed 23 October 2025](https://github.com/project-chip/connectedhomeip/blob/master/src/app/zap-templates/zcl/data-model/chip/content-control-cluster.xml)
- [Matter Alpha, Content Control cluster (secondary)](https://www.matteralpha.com/cluster/content-control)
- [Amazon Developer, Overview of Matter casting](https://developer.amazon.com/docs/fire-tv/overview-of-matter-casting.html)
- [Cloudflare, 1.1.1.1 for Families setup, 6 May 2026](https://developers.cloudflare.com/1.1.1.1/setup/)
- [NextDNS API](https://nextdns.github.io/api/)
- [IETF RFC 8484, DNS Queries over HTTPS, October 2018](https://www.rfc-editor.org/rfc/rfc8484)
- [Alston & Bird, California enacts digital age verification law, 23 October 2025 (secondary)](https://www.alstonprivacy.com/california-enacts-digital-age-verification-law/)
- [US Congress, S. 4159, Sammy's Law, text on GovInfo, 20 March 2026](https://www.govinfo.gov/content/pkg/BILLS-119s4159is/xhtml/BILLS-119s4159is.html)
- [Tech Policy Press, Sammy's Law tracker](https://techpolicy.press/tracker/sammys-law-of-2023-hr5778)
