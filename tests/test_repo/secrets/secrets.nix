let
testhost = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBiBw6GeAgYO2ZDwE7ZCHtXdI1mzP/F49ygjESd7cl22";
in
{
"hosts/testhost/secret.age".publicKeys = [ testhost ];
}