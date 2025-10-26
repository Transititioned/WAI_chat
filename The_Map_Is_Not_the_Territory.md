The Map Is Not the Territory - IT Service Mapping in Real Life

Frameworks are great until your infrastructure moves faster than your diagrams. Here’s why tag-based mapping might be the smarter play in 2025
Over the last year I’ve rolled out a few IT Services and Governance layers.  I was talking to a friend who’s a ServiceNow guru the other day and she mentioned their free CIS membership through VicGov might be in doubt. It made me think about how quickly the landscape around frameworks and panels shifts, and how that affects what’s practical to rollout.

Now this is delivery article on the ‘How’.  We’re not throwing out the baby.  CIS and ServiceNow are excellent ITSM and Security tools.  For mapping a combo, of top down, traffic based and tagging will be most effective.  But for now ,we’re talking tagging.

ServiceNow’s CIS course focuses on the classic top-down approach , tracing every dependency from the entry point down through the tech stack. Nice structure and it fits in nicely with their eTOM track if you’re in Telco. But in practice, most environments just don’t look like that anymore. And it makes for a very nice dashboard with click through.

But Modern infrastructure is a mix of on-prem, cloud, managed services, and APIs — half the time the thing you’re trying to map doesn’t even exist in the same way twice.

That’s why more teams I’ve worked with are leaning toward tag-based mapping instead. It’s lighter, faster to get the hot spots covered, and aligns better with how governance works today. When your tagging policy already captures ownership, environment, and data sensitivity, you can build something useful without waiting for a perfect auto-discovery run.

There’s some basic commonalities I’m seeing when implementing different framworks:

Frameworks make baselines easy, but they need to be applied locally and carefully
Map enough to understand risk and impact, not every dependency.
on’t design like it’s still the 2000s - your infrastructure moves faster than your diagrams do.
Big reports don’t get read.  If your reporting tools doesn’t report by exception its not fit for purpose.
How tagging works in MSP world

From MSP / cloud operations often manage many customer tenants and need automation, granular access control, and cross-tenant orchestration tools.
That feeds directly into your insight:

For standard customers, they license/tag at customer level.
If a customer wants their tools used, the MSP will often purchase those licenses only for that customer, and track them separately.
 

Trade-offs & gotchas to watch

Tag-based mapping is only as good as your tagging consistency. In environments with poor tag hygiene, maps will be noisy or incomplete.
Legacy systems (on-prem, older apps, third-party appliances) may not support tagging at all, requiring fallback mapping strategies.
For containers, microservices, APIs — ephemeral and dynamically instantiated — tag mapping works better, but you’ll still lose detail about internal dependencies (e.g. within a container).
Tagging is harder on-prem.  In practice, on-prem resources often lack tag metadata naturally, so you may have to retrofit tags via configuration, CMDB, or hybrid tools.
Monitoring / change drift: if the infra changes and tags aren’t maintained, your map becomes stale quickly.
Licensing granularity: MSPs may need to reconcile customer-specific licenses with shared tooling (e.g., a vendor module integrated only for one customer). That adds overhead.