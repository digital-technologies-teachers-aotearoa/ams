# Creates mock forum activity (users, topics, replies) for the marketing
# screenshot of the Community Forum capability on features.md.
#
# Run inside the Discourse container (not this repo's own containers --
# Discourse has its own separate database, entirely untouched by
# manage.py flush): copy this file in, then run it with `bin/rails runner`,
# Discourse's equivalent of `manage.py shell < script.py`. See
# docs/screenshots/seed-marketing.sh, which does exactly this.
#
# UNLIKE every other capture step in this suite, this one is NOT reset by
# reseeding and is NOT safe to run repeatedly without thought: Discourse has
# its own database that seed.sh/seed-marketing.sh never touch (see
# docs-conventions.md bullet 23). This script creates real, permanent
# Discourse users and posts -- accepted deliberately for this one marketing
# screenshot (unlike every other forum capture in this suite, which stays
# read-only on the Discourse side for exactly this reason). Every created
# user is prefixed "demo_" so this content stays identifiable as fixture
# data, not a real member, indefinitely. Idempotent-ish: safe to run more
# than once (finds existing users/topics/replies by name rather than
# duplicating them), but still permanent -- there is no reseed step that
# undoes it.

require "securerandom"

DEMO_PEOPLE = [
  { username: "demo_priya", name: "Priya Sharma" },
  { username: "demo_hemi", name: "Hemi Ngata" },
  { username: "demo_aroha", name: "Aroha Wilson" },
].freeze

users = DEMO_PEOPLE.map do |person|
  User.find_by(username: person[:username]) || User.create!(
    username: person[:username],
    name: person[:name],
    email: "#{person[:username]}@example.invalid",
    password: SecureRandom.hex(20),
    active: true,
    approved: true,
    trust_level: TrustLevel[1],
  ).tap(&:activate)
end

admin = User.find_by(username: "admin1") || Discourse.system_user
general_category_id = Category.find_by(slug: "general").id

TOPICS = [
  {
    title: "Anyone else marking exams this week?",
    raw: "Just checking in — how's everyone doing with the end-of-term " \
         "marking? I'm buried in scripts over here!",
    author: 0,
    replies: [
      { author: 1, raw: "Right there with you. Coffee levels critical." },
      { author: :admin, raw: "Hang in there, everyone — almost at the holidays!" },
    ],
  },
  {
    title: "New printable resource: times tables pack",
    raw: "I've just uploaded a new times tables practice pack to the " \
         "Resources section — free to use in your own classes.",
    author: 1,
    replies: [
      { author: 2, raw: "This looks brilliant, thank you for sharing!" },
    ],
  },
  {
    title: "Welcome to the community forum!",
    raw: "Welcome to everyone joining us here — introduce yourself and " \
         "let us know what you teach!",
    author: :admin,
    replies: [
      { author: 2, raw: "Hi all, I teach Year 9-10 maths in Wellington — excited to be here." },
      { author: 0, raw: "Welcome Aroha! Looking forward to swapping ideas." },
    ],
  },
].freeze

resolve = ->(ref) { ref == :admin ? admin : users[ref] }

TOPICS.each do |t|
  topic = Topic.find_by(title: t[:title])
  first_post = if topic
    topic.first_post
  else
    PostCreator.create!(
      resolve.call(t[:author]),
      title: t[:title],
      raw: t[:raw],
      category: general_category_id,
      skip_validations: true,
    )
  end

  t[:replies].each do |r|
    reply_author = resolve.call(r[:author])
    next if first_post.topic.posts.where(user_id: reply_author.id).exists?

    PostCreator.create!(
      reply_author,
      topic_id: first_post.topic_id,
      raw: r[:raw],
      skip_validations: true,
    )
  end
end

puts "Marketing forum fixture data ready: #{DEMO_PEOPLE.size} demo users, #{TOPICS.size} topics."
