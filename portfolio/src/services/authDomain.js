export const allowedSchoolEmailDomain = "sdh.hs.kr";

export const isAllowedSchoolEmail = (email = "") =>
  String(email).trim().toLowerCase().endsWith(`@${allowedSchoolEmailDomain}`);
