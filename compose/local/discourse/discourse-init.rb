# discourse-init.rb
# Idempotent Discourse site settings + admin creation.
# This helps setup Discourse in a developer environment.
# Saves all attributes with validations; only password may be written with validate: false

# ---!!!--- NOT RECOMMENDED FOR PRODUCTION USE ---!!!---

require 'securerandom'
puts "Starting Discourse init script..."

def cast_value(v)
  case v
  when String
    s = v.strip
    return true if s.downcase == 'true'
    return false if s.downcase == 'false'
    Integer(s) rescue v
  else
    v
  end
end

# Settings that must be set first (dependency-aware)
ordered_settings = [
  ['email_editable', false],
  ['discourse_connect_url', 'http://localhost:3000/forum/sso'],
  ['discourse_connect_secret', 'changeme']
]

# Other settings
more_settings = {
  'title' => 'AMS Forums',
  'invite_only' => false,
  'login_required' => true,
  'allow_new_registrations' => false,
  'enable_signup_cta' => false,
  'auth_skip_create_confirm' => true,
  'auth_overrides_email' => true,
  'auth_overrides_username' => true,
  'auth_overrides_name' => true,
  'enable_discourse_connect' => true,
  'discourse_connect_overrides_bio' => true,
  'discourse_connect_overrides_avatar' => true,
  'discourse_connect_overrides_profile_background' => true,
  'discourse_connect_overrides_location' => true,
  'discourse_connect_overrides_website' => true,
  'discourse_connect_overrides_card_background' => true,
  'gravatar_enabled' => false,
  'automatically_download_gravatars' => false,
  'logout_redirect' => 'http://localhost:3000',
  'pending_users_reminder_delay_minutes' => 5,
  'default_trust_level' => 1,
  'allowed_iframes' => 'https://www.google.com/maps/embed?|https://www.openstreetmap.org/export/embed.html?|https://calendar.google.com/calendar/embed?|https://codepen.io/*/embed/preview/|https://www.instagram.com/|https://open.spotify.com/|http://localhost/discobot/certificate.svg',
  'default_navigation_menu_categories' => '2|3|4',
  'default_composer_category' => 4,
  'bootstrap_mode_min_users' => 0,
  'default_email_digest_frequency' => 1440,
  'assign_allowed_on_groups' => 3
}

# Apply ordered settings first
ordered_settings.each do |k, v|
  begin
    SiteSetting.send("#{k}=", cast_value(v))
    puts "Set #{k} = #{cast_value(v).inspect}"
  rescue => e
    puts "Failed to set #{k}: #{e.class}: #{e.message}"
  end
end

# Apply remaining settings
more_settings.each do |k, v|
  begin
    SiteSetting.send("#{k}=", cast_value(v))
    puts "Set #{k} = #{cast_value(v).inspect}"
  rescue => e
    puts "Failed to set #{k}: #{e.class}: #{e.message}"
  end
end

# -----------------------
# Admin user creation/update
# -----------------------
admin_email    = ENV['DISCOURSE_ADMIN_EMAIL']    || 'admin@example.com'
admin_username = ENV['DISCOURSE_ADMIN_USERNAME'] || 'admin'
provided_pass  = ENV['DISCOURSE_ADMIN_PASSWORD'] || nil
creds_path     = "/shared/admin_credentials.txt"

def persist_credentials(path, username, email, password)
  begin
    File.open(path, "a") do |f|
      f.puts "=== Discourse admin credentials (created/updated #{Time.now.utc}) ==="
      f.puts "username: #{username}"
      f.puts "email:    #{email}"
      f.puts "password: #{password}"
      f.puts ""
    end
    puts "Wrote admin credentials to #{path}"
  rescue => e
    puts "Failed to write credentials to #{path}: #{e.class}: #{e.message}"
  end
end

# Helper to detect password-related validation messages we should override
def password_issue?(user)
  return false unless user.respond_to?(:errors) && user.errors.any?
  user.errors.full_messages.any? do |m|
    m =~ /common password|too common|is one of the/i || m =~ /too short|minimum is \d+ characters/i
  end
end

begin
  user = nil

  # Try to find by email if column exists, else username
  if User.respond_to?(:column_names) && User.column_names.include?('email')
    user = User.find_by(email: admin_email) rescue nil
  end
  user ||= User.find_by(username: admin_username) rescue nil

  if user
    puts "Admin user exists (id=#{user.id}, username=#{user.username}, email=#{user.respond_to?(:email) ? user.email.inspect : 'n/a'})"

    # Optionally reset password if provided
    if provided_pass && provided_pass.strip != ""
      puts "Attempting password update for existing admin..."
      if user.respond_to?(:password=)
        user.password = provided_pass
        begin
          user.save!
          puts "Password updated successfully with normal validation."
          persist_credentials(creds_path, admin_username, admin_email, provided_pass)
        rescue ActiveRecord::RecordInvalid => e
          if password_issue?(user)
            puts "Password rejected (common/too short). Falling back to save(validate: false) to set password only."
            user.password = provided_pass
            user.save(validate: false)
            puts "Password updated using save(validate: false)."
            persist_credentials(creds_path, admin_username, admin_email, provided_pass)
          else
            puts "Failed to update password: #{e.class}: #{e.message}"
            puts "Validation errors: #{user.errors.full_messages.join('; ')}" if user.respond_to?(:errors)
          end
        end
      else
        puts "User model does not support setting password on this Discourse version; skipping password update."
      end
    else
      puts "No new password provided via DISCOURSE_ADMIN_PASSWORD; not modifying password."
    end

  else
    # Create new user. Strategy:
    # - If provided_pass: try create with it; if rejected due to password issues, create with strong temporary password then replace with save(validate:false)
    # - If no provided_pass: create with generated strong password
    generated_password = SecureRandom.hex(16) # 32-char hex = strong

    if provided_pass && provided_pass.strip != ""
      puts "Creating admin with provided password (may be rejected by validators)..."
      user = User.new
      user.username = admin_username
      user.name = 'Admin' if user.respond_to?(:name=)
      user.email = admin_email if user.respond_to?(:email=)
      user.password = provided_pass if user.respond_to?(:password=)
      user.active = true if user.respond_to?(:active=)
      user.approved = true if user.respond_to?(:approved=)
      user.email_confirmed = true if user.respond_to?(:email_confirmed=)

      begin
        user.save!
        puts "Created user id=#{user.id} with provided password."
        persist_credentials(creds_path, admin_username, admin_email, provided_pass)
      rescue ActiveRecord::RecordInvalid => e
        if password_issue?(user)
          puts "Provided password rejected (common/too short). Creating with a strong temporary password and then replacing password via save(validate: false)."
          temp_user = User.new
          temp_user.username = admin_username
          temp_user.name = 'Admin' if temp_user.respond_to?(:name=)
          temp_user.email = admin_email if temp_user.respond_to?(:email=)
          temp_user.password = generated_password if temp_user.respond_to?(:password=)
          temp_user.active = true if temp_user.respond_to?(:active=)
          temp_user.approved = true if temp_user.respond_to?(:approved=)
          temp_user.email_confirmed = true if temp_user.respond_to?(:email_confirmed=)

          begin
            temp_user.save!
            puts "Created user id=#{temp_user.id} with strong temporary password."
            # Now replace weak provided password by bypassing validations
            if temp_user.respond_to?(:password=)
              temp_user.password = provided_pass
              temp_user.save(validate: false)
              puts "Replaced password using save(validate: false)."
              persist_credentials(creds_path, admin_username, admin_email, provided_pass)
              user = temp_user
            else
              puts "Cannot set password on this Discourse version; leaving temporary password in place."
              persist_credentials(creds_path, admin_username, admin_email, generated_password)
              user = temp_user
            end
          rescue => e2
            puts "Failed to create user with temporary password: #{e2.class}: #{e2.message}"
            if temp_user.respond_to?(:errors) && temp_user.errors.any?
              puts "Validation errors: #{temp_user.errors.full_messages.join('; ')}"
            end
          end
        else
          puts "Failed to create user with provided password: #{e.class}: #{e.message}"
          if user.respond_to?(:errors) && user.errors.any?
            puts "Validation errors: #{user.errors.full_messages.join('; ')}"
          end
        end
      end

    else
      # No provided password — create with generated strong password
      puts "Creating admin with generated strong password."
      user = User.new
      user.username = admin_username
      user.name = 'Admin' if user.respond_to?(:name=)
      user.email = admin_email if user.respond_to?(:email=)
      user.password = generated_password if user.respond_to?(:password=)
      user.active = true if user.respond_to?(:active=)
      user.approved = true if user.respond_to?(:approved=)
      user.email_confirmed = true if user.respond_to?(:email_confirmed=)
      begin
        user.save!
        puts "Created user id=#{user.id}."
        persist_credentials(creds_path, admin_username, admin_email, generated_password)
      rescue => e
        puts "Failed to create user: #{e.class}: #{e.message}"
        if user.respond_to?(:errors) && user.errors.any?
          puts "Validation errors: #{user.errors.full_messages.join('; ')}"
        end
      end
    end
  end

  # Promote to admin if creation succeeded or user existed
  if user && user.respond_to?(:persisted?) && user.persisted?
    begin
      if user.respond_to?(:admin=)
        unless user.admin?
          user.admin = true
          user.save!
          puts "Granted admin to #{user.username}"
        else
          puts "User already admin."
        end
      elsif user.respond_to?(:grant_admin!)
        user.grant_admin!
        puts "Called grant_admin!"
      else
        puts "Cannot programmatically promote on this Discourse version. Promote manually if needed."
      end
    rescue => e
      puts "Failed to promote user to admin: #{e.class}: #{e.message}"
    end
  else
    puts "Skipping admin promotion because user does not exist or wasn't persisted."
  end

rescue => e
  puts "Admin creation/update failed: #{e.class}: #{e.message}"
  puts e.backtrace.first(8)
end

puts "Discourse init script finished."
