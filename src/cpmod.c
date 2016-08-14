
#include <dirent.h>
#include <sys/stat.h>
#include <unistd.h>

#ifndef FALSE
#define FALSE 0
#endif
#ifndef TRUE
#define TRUE 1
#endif

typedef enum {
    OTHER,
    GROUP,
    OWNER
} pset_t;

// #define pset_to_mask(pset) ((mote_t)((pset) * 3))

static int cpmod_mask(pset_t pset, int mask)
{
    switch (pset)
    {
        case OTHER:
            return mask & 07;
        case GROUP:
            return (mask & 07) << 3;
        case OWNER:
            return (mask & 07) << 6;
    }
}

static int cpmod_isowner(const struct stat * info)
{
    return info->st_uid == geteuid();
}

static int cpmod_exist(const char * path, int follow_symlink)
{
    struct stat info;
    if (lstat(path, &info) == 0)
    {
        if ((info.st_mode & S_IFLNK) && !follow_symlink) return FALSE;
        return cpmod_isowner(&info);
    }
    return FALSE;
}

static int cpmod_isdir(const struct stat * info)
{
    return (info->st_mode & S_IFDIR);
}

static int cpmod_isfile(const struct stat * info)
{
    return (info->st_mode & S_IFREG);
}

static int cpmod_get_perm(const struct stat * info, pset_t pset, int mask)
{
    int     perm;

    perm = info->st_mode & cpmod_mask(pset, mask);

    switch (pset) {
        case OTHER:
            return perm;
        case GROUP:
            return (perm >> 3);
        case OWNER:
            return (perm >> 6);
    }
    return 0;
}

static void cpmod_set_perm(int fd, pset_t pset, int mask, int new_perms)
{
    struct stat info;
    mode_t      new_mode;

    if ((new_perms & 07) != new_perms) return;

    fstat(fd, &info);
    new_mode = info.st_mode & ~cpmod_mask(pset, mask);

    switch (pset)
    {
        case OTHER:
            new_mode |= new_perms;
            break;
        case GROUP:
            new_mode |= (new_perms << 3);
            break;
        case OWNER:
            new_mode |= (new_perms << 6);
            break;
    }

    fchmod(fd, new_mode);
}

static int cpmod_cpmod(int fd, pset_t src_pset, pset_t tar_pset, int mask)
{
    int             perms;
    struct stat     info;

    if (fstat(fd, &info) == -1) return -1;

    perms = cpmod_get_perm(&info, src_pset, mask);
    cpmod_set_perm(fd, tar_pset, mask, perms);

    return 0;
}

static int cpmod_cpmoddir(DIR * dirp)
{
    
}

int main(int argc, const char ** argv)
{
    return 0;
}
