# Fix Profile Image Storage Issue

## Current Problem
- Profile images are being uploaded to Cloudinary and full URLs stored in Django's ImageField
- ImageField expects relative paths, not full URLs
- Template uses {{ usuario.imagen_usuario.url }} which prepends MEDIA_URL to the stored path
- Results in malformed URLs like /media/https:/res.cloudinary.com/...

## Tasks
- [ ] Modify `actualizar_foto_perfil` function in `Proyecto/App/views/auth.py`
  - Remove Cloudinary import and usage
  - Save image directly to ImageField using local storage
  - Keep image validation
- [ ] Test that images are saved to `media/usuarios/` directory
- [ ] Verify template displays images correctly
- [ ] Update any related tests if needed
